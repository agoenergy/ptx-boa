##### Results of the optimization model

We use an optimization model to determine the capacities and full load hours of generators, electrolyzers, derivative production facilitites and storage. The model calculates capacities and hourly dispatch for eight representative weeks while minimizing total costs. PyPSA is used for modeling. The tsam package is used for temporal aggregation.

Model runs are pre-calculated for all default settings. If you modify the input data in **Data editing mode**, a live recalculation is triggered for the settings you selected in the sidebar. For all other cost calculations that are shown in the cost comparison graphs, the modified data is used to calculate the costs, but we use the full load hours from the default scenario to cut down computational costs.

In this sheet you can explore the generation profiles for the currently selected scenario. You can also download the PyPSA model as a netcdf file and use it as a starting point for your own modeling exercises.
