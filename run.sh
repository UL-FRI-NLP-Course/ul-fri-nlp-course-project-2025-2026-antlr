#!/bin/bash
#SBATCH --job-name=anltr_db
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=logs/db_simple_%j.log

# Setup paths
PERM_DATA="$(pwd)/.database"
PGDATA_LOCAL="/tmp/postgres_data_$SLURM_JOB_ID"
PGSOCKET_LOCAL="/tmp/postgres_sock_$SLURM_JOB_ID"

mkdir -p "$PERM_DATA"
mkdir -p "$PGDATA_LOCAL" "$PGSOCKET_LOCAL"
chmod 700 "$PGDATA_LOCAL" "$PGSOCKET_LOCAL"

# Check if we need to fill the data
# Logic: If directory is empty, we MUST insert. If not, we only insert if flag is passed.
RUN_INSERT=false
if [ -z "$(ls -A "$PERM_DATA")" ]; then
    echo "Permanent storage is empty. Will run insert script."
    RUN_INSERT=true
elif [[ "$1" == "--force-data-refresh" ]]; then
    echo "Force refresh detected. Will run insert script."
    RUN_INSERT=true
else
    echo "Found existing data in $PERM_DATA. Skipping insert script (use --force-data-refresh to override)."
fi

# Restore data from permanent storage to local /tmp (if it exists)
if [ "$(ls -A "$PERM_DATA")" ]; then
    echo "Restoring existing database from $PERM_DATA to local storage..."
    cp -r "$PERM_DATA"/* "$PGDATA_LOCAL/"
fi

# Ensure image is present
if [ ! -f "timescaledb.sif" ]; then
    echo "Pulling TimescaleDB image..."
    apptainer pull timescaledb.sif docker://timescale/timescaledb:latest-pg16
fi

# Check if .env file exists, otherwise
# copy example and warn user
if [ ! -f ".env" ]; then
    echo "No .env file found. Creating example one ..."
    cp .env.example .env
fi
# Extract passwrd and db from .env TIMESCALE_SERVICE_URL and set env vars for Postgres
DB_NAME=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/([^?]+).*/\1/')
DB_USER=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/\/([^:]+):.*/\1/')
DB_PASS=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/\/[^:]+:([^@]+)@.*/\1/')

# Start Postgres in background
apptainer run \
    -B "$PGDATA_LOCAL":/var/lib/postgresql/data \
    -B "$PGSOCKET_LOCAL":/var/run/postgresql \
    --env POSTGRES_DB=$DB_NAME \
    --env POSTGRES_PASSWORD=$DB_PASS \
    --env POSTGRES_USER=$DB_USER \
    timescaledb.sif \
    -c unix_socket_directories='/var/run/postgresql' &

# Wait for it to be ready
echo "Waiting for Postgres to start up ..."
until apptainer exec timescaledb.sif pg_isready -h localhost -U postgres; do
    sleep 2
done
echo "Postgres is READY!"

# Setup Connection string
BASE_URL=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2-)
if [[ "$BASE_URL" == *"?"* ]]; then
    export TIMESCALE_SERVICE_URL="${BASE_URL}&host=$PGSOCKET_LOCAL"
else
    export TIMESCALE_SERVICE_URL="${BASE_URL}?host=$PGSOCKET_LOCAL"
fi
echo "Connection string updated with dynamic socket: $TIMESCALE_SERVICE_URL"

# Check if .venv exists, otherwise create it and install requirements
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment and installing requirements..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install timescale-vector==0.0.7 --no-deps
else
    echo "Virtual environment already exists. Activating..."
fi

source .venv/bin/activate

# Install extensions
apptainer exec timescaledb.sif psql -h localhost -U postgres -d antlrgres -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run Fill Script if required
if [ "$RUN_INSERT" = true ]; then
    echo "Filling db with script..."
    python src/rag/app/insert_vectors.py
fi

# EXAMPLE: TODO: Similarity Search
echo "-=-=-=-= Successfully set up database and environment! =-=-=-=-"
echo ""
echo ""
echo "Running similarity search script..."
python src/rag/app/similarity_search.py

# SHUTDOWN AND PERSIST
echo "Shutting down Postgres cleanly..."
# Using pg_ctl stop ensures all data is flushed to disk before we copy it
apptainer exec timescaledb.sif pg_ctl -D /var/lib/postgresql/data stop

echo "Syncing data from /tmp back to permanent storage ($PERM_DATA)..."
# Use rsync or cp to move the updated files back to home
cp -r "$PGDATA_LOCAL"/* "$PERM_DATA/"

echo "Data persisted. Cleaning up /tmp..."
rm -rf "$PGDATA_LOCAL" "$PGSOCKET_LOCAL"

echo "Job finished."
