#!/bin/bash

echo "Starting parameter sweep pipeline"
echo "================================="

echo ""
echo "Step 1: Coarse grid [-5, 5, 0.5] x [0, 1, 0.05]"
python plant_gravitropism.py --Gmin -5 --Gmax 5 --Gstep 0.5 \
	    --amin 0 --amax 1 --astep 0.05 --num_workers 48 && \

echo ""
echo "Step 2: G=0 fine alpha sweep [0, 1, 0.01]"
python plant_gravitropism.py --Gmin 0 --Gmax 0 --Gstep 1 \
	    --amin 0 --amax 1 --astep 0.01 --num_workers 48 && \

echo ""
echo "Step 3: Smart run 1 (wide, top 3, mesh 10)"
python plant_gravitropism.py --smart --smartNumPoints 3 \
	    --smartGridSize 2 --smartGridMesh 10 --num_workers 48 && \

echo ""
echo "Step 4: Smart run 2 (wide, top 2, mesh 10)"
python plant_gravitropism.py --smart --smartNumPoints 2 \
	    --smartGridSize 2 --smartGridMesh 10 --num_workers 48 && \

echo ""
echo "Step 5: Smart run 3 (narrow, top 1, mesh 20)"
python plant_gravitropism.py --smart --smartNumPoints 1 \
	    --smartGridSize 1 --smartGridMesh 20 --num_workers 48

echo ""
echo "Pipeline complete."
