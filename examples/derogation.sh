#!/bin/bash

# Pod name (used in room name)
export POD_NAME="pod-Demo"

# User info (email @ used in Cisco Spark)
export E2E=""
export T200=""
export T300=""
export T400=""

# Admin settings
export CHAT_ROOM_MODERATORS=""
export CISCO_SPARK_TOKEN=""

# Cisco Spark bot token
export CISCO_SPARK_BOT_NAME=""
export CISCO_SPARK_BOT_TOKEN=""

# Shellbot settings
export SERVER_PORT=8080
export SERVER_HOST=""
export SERVER_URL="http://${SERVER_HOST}:${SERVER_PORT}"
export SERVER_HOOK="/hook/${POD_NAME}"
export SERVER_TRIGGER="/trigger"
export SERVER_LOG="./log/derogation-${POD_NAME}.log"

# Run the script given in the first arg
python ${1}

exit 0
