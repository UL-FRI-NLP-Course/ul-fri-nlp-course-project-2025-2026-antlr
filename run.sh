#!/bin/bash
#SBATCH --job-name=anltr_db
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=logs/db_log.log

# Big text je bil narjen z https://fsymbols.com/generators/tarty/

# label:
GREEN='\033[0;32m'
NC='\033[0m'
log_label="${GREEN}run${NC}"
# --


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
    echo -e "[${log_label}] Permanent storage is empty. Will run insert script."
    RUN_INSERT=true
elif [[ "$1" == "--force-data-refresh" ]]; then
    echo -e "[${log_label}] Force refresh detected. Will run insert script."
    RUN_INSERT=true
else
    echo -e "[${log_label}] Found existing data in $PERM_DATA. Skipping insert script (use --force-data-refresh to override)."
fi

# Restore data from permanent storage to local /tmp (if it exists)
if [ "$(ls -A "$PERM_DATA")" ]; then
    echo -e "[${log_label}] Restoring existing database from $PERM_DATA to local storage..."
    cp -r "$PERM_DATA"/* "$PGDATA_LOCAL/"
fi

# Ensure image is present
if [ ! -f "timescaledb.sif" ]; then
    echo -e "[${log_label}] Pulling TimescaleDB image..."
    apptainer pull timescaledb.sif docker://timescale/timescaledb:latest-pg16
fi

# Check if .env file exists, otherwise
# copy example and warn user
if [ ! -f ".env" ]; then
    echo -e "[${log_label}] No .env file found. Creating example one ..."
    cp example.env .env
fi
# Extract passwrd and db from .env TIMESCALE_SERVICE_URL and set env vars for Postgres
DB_NAME=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/([^?]+).*/\1/')
DB_USER=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/\/([^:]+):.*/\1/')
DB_PASS=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/\/[^:]+:([^@]+)@.*/\1/')
DB_TABLE=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2- | sed -E 's/.*\/([^?]+).*/\1/')

# Start Postgres in background (also lower max memory allocation)
apptainer run \
    -B "$PGDATA_LOCAL":/var/lib/postgresql/data \
    -B "$PGSOCKET_LOCAL":/var/run/postgresql \
    --env POSTGRES_DB=$DB_NAME \
    --env POSTGRES_PASSWORD=$DB_PASS \
    --env POSTGRES_USER=$DB_USER \
    timescaledb.sif \
    -c unix_socket_directories='/var/run/postgresql' \
    -c shared_buffers=1GB \
    -c max_connections=20 \
    -c work_mem=16MB \
    -c huge_pages=off &

# Wait for it to be ready
echo -e "[${log_label}] Waiting for Postgres to start up ..."
until apptainer exec timescaledb.sif pg_isready -h localhost -U postgres; do
    sleep 2
done
echo ""
echo ""
echo "██████╗░██████╗░  ██████╗░███████╗░█████╗░██████╗░██╗░░░██╗"
echo "██╔══██╗██╔══██╗  ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗░██╔╝"
echo "██║░░██║██████╦╝  ██████╔╝█████╗░░███████║██║░░██║░╚████╔╝░"
echo "██║░░██║██╔══██╗  ██╔══██╗██╔══╝░░██╔══██║██║░░██║░░╚██╔╝░░"
echo "██████╔╝██████╦╝  ██║░░██║███████╗██║░░██║██████╔╝░░░██║░░░"
echo "╚═════╝░╚═════╝░  ╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═════╝░░░░╚═╝░░░"
echo ""
echo ""

# Setup Connection string
BASE_URL=$(grep '^TIMESCALE_SERVICE_URL=' .env | cut -d '=' -f2-)
if [[ "$BASE_URL" == *"?"* ]]; then
    export TIMESCALE_SERVICE_URL="${BASE_URL}&host=$PGSOCKET_LOCAL"
else
    export TIMESCALE_SERVICE_URL="${BASE_URL}?host=$PGSOCKET_LOCAL"
fi
# echo -e "Connection string updated with dynamic socket: $TIMESCALE_SERVICE_URL"

# Check if .venv exists, otherwise create it and install requirements
if [ ! -d ".venv" ]; then
    echo -e "[${log_label}] Creating virtual environment and installing requirements..."
    echo " "
    echo " "
    echo " ░█████╗░██████╗░███████╗░█████╗░████████╗██╗███╗░░██╗░██████╗░  ██╗░░░██╗███████╗███╗░░██╗██╗░░░██╗"
    echo " ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║████╗░██║██╔════╝░  ██║░░░██║██╔════╝████╗░██║██║░░░██║"
    echo " ██║░░╚═╝██████╔╝█████╗░░███████║░░░██║░░░██║██╔██╗██║██║░░██╗░  ╚██╗░██╔╝█████╗░░██╔██╗██║╚██╗░██╔╝"
    echo " ██║░░██╗██╔══██╗██╔══╝░░██╔══██║░░░██║░░░██║██║╚████║██║░░╚██╗  ░╚████╔╝░██╔══╝░░██║╚████║░╚████╔╝░"
    echo " ╚█████╔╝██║░░██║███████╗██║░░██║░░░██║░░░██║██║░╚███║╚██████╔╝  ░░╚██╔╝░░███████╗██║░╚███║░░╚██╔╝░░"
    echo " ░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚═╝╚═╝░░╚══╝░╚═════╝░  ░░░╚═╝░░░╚══════╝╚═╝░░╚══╝░░░╚═╝░░░"
    echo " "
    echo " "
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install timescale-vector==0.0.7 --no-deps
else
    echo -e "[${log_label}] Virtual environment already exists. Activating..."
fi

source .venv/bin/activate

# Install extensions
apptainer exec timescaledb.sif psql -h localhost -U postgres -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run Fill Script if required
if [ "$RUN_INSERT" = true ]; then
    echo -e "[${log_label}] Filling db with script..."
    echo ""
    echo "█▀▀ █ █░░ █░░ █ █▄░█ █▀▀   █▀▄ ▄▀█ ▀█▀ ▄▀█ █▄▄ ▄▀█ █▀ █▀▀"
    echo "█▀░ █ █▄▄ █▄▄ █ █░▀█ █▄█   █▄▀ █▀█ ░█░ █▀█ █▄█ █▀█ ▄█ ██▄"
    echo ""
    python src/rag/app/insert_vectors.py
fi

# EXAMPLE: TODO: Similarity Search
echo -e "[${log_label}] -=-=-=-= Successfully set up database and environment! =-=-=-=-"
# echo -e ""
# echo -e ""
# echo -e "[${log_label}] Running similarity search script..."
# python src/rag/app/similarity_search.py


echo ""
echo ""
echo "██████╗░███████╗███████╗███████╗██████╗░░█████╗░████████╗  ██████╗░░█████╗░████████╗"
echo "██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝"
echo "██████╔╝█████╗░░█████╗░░█████╗░░██████╔╝███████║░░░██║░░░  ██████╦╝██║░░██║░░░██║░░░"
echo "██╔══██╗██╔══╝░░██╔══╝░░██╔══╝░░██╔══██╗██╔══██║░░░██║░░░  ██╔══██╗██║░░██║░░░██║░░░"
echo "██║░░██║███████╗██║░░░░░███████╗██║░░██║██║░░██║░░░██║░░░  ██████╦╝╚█████╔╝░░░██║░░░"
echo "╚═╝░░╚═╝╚══════╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░  ╚═════╝░░╚════╝░░░░╚═╝░░░"
echo ""
echo ""

HOST=$(hostname)
PORT=8080

echo "SSH tunnel command:"
echo "ssh -L $PORT:$HOST:$PORT $USER@hpc-login.arnes.si"
echo ""
echo "Then open: http://localhost:$PORT"
python src/rag/app/server.py --port $PORT


# SHUTDOWN AND PERSIST
echo -e "[${log_label}] Shutting down Postgres cleanly..."
# Using pg_ctl stop ensures all data is flushed to disk before we copy it
apptainer exec timescaledb.sif pg_ctl -D /var/lib/postgresql/data stop

echo -e "[${log_label}] Syncing data from /tmp back to permanent storage ($PERM_DATA)..."
# Use rsync or cp to move the updated files back to home
cp -r "$PGDATA_LOCAL"/* "$PERM_DATA/"

echo -e "[${log_label}] Data persisted. Cleaning up /tmp..."
rm -rf "$PGDATA_LOCAL" "$PGSOCKET_LOCAL"

echo -e "[${log_label}] Job finished."
