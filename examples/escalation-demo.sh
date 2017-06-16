#!/bin/bash
#######################################################################
# What: Configuration file to set the escalation environment process
# How: To use with escalation.py script provided for the shellbot
#      micro framework: https://github.com/bernard357/shellbot
# Run:
#   After have installed shellbot and run the demo succesfully,
#   run one of the following command according to your need:
#   * dev : ./escalation-demo.sh escalation.py
#   * prod: set apache WSGI server to run it as web server
#           and include these constantes in the virtual host
# Trigger: It is done by web request on the trigger url:
#  > curl http://${SERVER_HOST}:${SERVER_PORT}/trigger/${POD_NAME}
#  ie: http://myserver.com:8080/trigger/demo
#      with:
#        SERVER_HOST = myserver.com
#        SERVER_PORT = 8080
#        POD_NAME = demo
# Log: Local file dedicated to this setting (./escalation_${POD_NAME.log)
#   ie: ./escalation-demo.log
#######################################################################

# Pod name (used in room name)
export POD_NAME="demo"

# User info
export SHOP_FLOOR="shop.floor@myserver.com"
export STRESS_ENGINEER="stress.engineer@myserver.com"
export DESIGN_ENGINEER="design.engineer@myserver.com"

# Admin settings
## Admin email Cisco Spark account
export CHAT_ROOM_MODERATORS="admin@myserver.com"

## Admin Cisco spark token
export CISCO_SPARK_TOKEN=""

# Cisco Spark bot token
export CISCO_SPARK_BOT_TOKEN=""

# Shellbot settings
export SERVER_PORT=8080
export SERVER_HOST="myserver.com"
export SERVER_URL="http://${SERVER_HOST}:${SERVER_PORT}"
export SERVER_HOOK="/hook/${POD_NAME}"
export SERVER_TRIGGER="/trigger/${POD_NAME}"
export SERVER_LOG="./escalation-${POD_NAME}.log"

# Run the script given in the first arg
python ${1}

exit 0
