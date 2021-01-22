#!/usr/bin/env bash
docker run -it --rm --name axl -p 8888:8888 \
    --mount type=bind,src="$(pwd)",dst=/home/jovyan \
    jeokrohn/axl_workshop