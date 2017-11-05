#!/bin/bash
screen -dm -S dbl_ltc python candles.py -e -m _dbl_ltc -s 10 -l 21 -i 60 --sT 0.0 --bT 0.1
screen -dm -S ezc_ltc python candles.py -e -m _ezc_ltc -s 20 -l 50 -i 120 --sT 0 --bT 0 
screen -dm -S xnc_ltc python candles.py -e -m _xnc_ltc -s 50 -l 200 -i 60 --sT -0.1 --bT 0.0

screen -dm -S mem_ltc python candles.py -e -m _mem_ltc -s 20 -l 50 -i 60 --sT 0.0 --bT 0.0
screen -dm -S gld_ltc python candles.py -e -m _gld_ltc -s 50 -l 200 -i 30 --sT -0.1 --bT 0.25
screen -dm -S src_btc python candles.py -e -m _src_btc -s 10 -l 21 -i 240 --sT 0.0 --bT 0.0
screen -dm -S cpr_ltc python candles.py -e -m _cpr_ltc -s 10 -l 21 -i 30 --sT 0 --bT 0.25
screen -dm -S hyc_btc python candles.py -e -m _hyc_btc -s 20 -l 50 -i 60 --bT 0 --sT 0
screen -dm -S ifc_ltc python candles.py -e -m _ifc_ltc -s 5 -l 8 -i 240 --bT 0.1 -sT 0
