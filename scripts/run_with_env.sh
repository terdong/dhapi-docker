#!/bin/bash

# 컨테이너 환경변수를 내보내기
export $(cat /proc/1/environ | xargs -0)

/usr/local/bin/python /app/lotto_generator.py "$LOTTO_NUMBERS"