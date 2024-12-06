#!/bin/sh

curl -X POST "http://${SITE_DOMAIN}/api/v1/notebook/remove_inactives/" -H "Accept: application/json" -H "Content-Type: application/json"