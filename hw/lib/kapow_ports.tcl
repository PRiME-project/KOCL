# PRiME KAPow QSys system port description
# Adds KAPow control ports to kernel system QSys component. This script gets sourced, not executed directly, so <kernel> is inherited from parent script
# James Davis, 2015

add_interface ${kernel}_kapow_clk clock sink
add_interface_port ${kernel}_kapow_clk ${kernel}_kapow_clk clk Input 1

add_interface ${kernel}_kapow conduit end
add_interface_port ${kernel}_kapow ${kernel}_kapow_cnten cnten Input 1
add_interface_port ${kernel}_kapow ${kernel}_kapow_scanin scanin Input 1
add_interface_port ${kernel}_kapow ${kernel}_kapow_scanout scanout Output 1