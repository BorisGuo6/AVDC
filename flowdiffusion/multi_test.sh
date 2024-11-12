for i in {1..10}
do
    python train_mw.py --mode inference -c 4 -p ../examples/knot-simulation-tie$i.png -d knot-simulation-tie -t knot-simulation-tie
done