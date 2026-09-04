# Shadow Detector Simulation Sandbox

## Overview
The Shadow Detection Sandbox allows risk teams to test candidate fraud rules against historical transaction streams in a strictly read-only environment.

## Ground Truth Handling
* When confirmed fraud investigation verdicts are available ($\ge 5$), the simulator computes empirical precision and recall.
* When ground truth is insufficient, the system explicitly reports `INSUFFICIENT_GROUND_TRUTH` with False Positive Rate and novel firing volume.
