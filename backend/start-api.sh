# Load environment variables from the .env file
source .env

# Redis conf file
REDIS_CONF="/etc/redis/redis.conf"

# Stop the Redis service if it is running as a service
sudo service redis stop

# Check if Redis server is already running
if pgrep -x "redis-server" > /dev/null
then
    echo "Redis server is already running. Skipping start..."
else
    # Check if 'maxmemory' is already set to 100mb
    if ! sudo grep -q '^maxmemory 100mb' $REDIS_CONF; then
        sudo cp $REDIS_CONF $REDIS_CONF.bak
        sudo sed -i 's/^# *maxmemory .*/maxmemory 100mb/' $REDIS_CONF
        echo "maxmemory updated to 100mb."
    else
        echo "maxmemory is already set to 100mb."
    fi

    # Check if 'maxmemory-policy' is already set to allkeys-lru
    if ! sudo grep -q '^maxmemory-policy allkeys-lru' $REDIS_CONF; then
        sudo sed -i 's/^# *maxmemory-policy .*/maxmemory-policy allkeys-lru/' $REDIS_CONF
        echo "maxmemory-policy updated to allkeys-lru."
    else
        echo "maxmemory-policy is already set to allkeys-lru."
    fi
        echo "Starting Redis server..."
        sudo redis-server $REDIS_CONF --loadmodule ~/redis-stack-server/lib/redisbloom.so --daemonize yes
    fi

# Check the ENVIRONMENT variable from the .env file and run FastAPI accordingly
if [ "$ENVIRONMENT" = "development" ];
then
    fastapi dev app/main.py
else
    fastapi run app/main.py
fi
