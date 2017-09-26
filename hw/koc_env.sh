## Script to set up environmental variabls for Quartus and AOC

# Change this to your Altera install directory
ALTERA="/mnt/applications/altera/15.0"

# Export Altera root
export ALTERAROOT=$ALTERA
# Export Altera AOCL SDK root
export ALTERAOCLSDKROOT=$ALTERAROOT"/hld"
# Export AOCL board package root
export AOCL_BOARD_PACKAGE_ROOT=$ALTERAOCLSDKROOT"/board/c5soc"
# Force use of compatible Quartus version
export QUARTUS_ROOTDIR=$ALTERAROOT"/quartus"
export QUARTUS_ROOTDIR_OVERRIDE=$QUARTUS_ROOTDIR
# Add ARM GCC to path
export PATH=$ALTERAROOT"/embedded/ds-5/sw/gcc/bin:"$PATH
# Add Quartus bin to path
export PATH=$ALTERAROOT"/quartus/bin:"$PATH
# Add Altera OpenCL SDK to path
export PATH=$ALTERAROOT"/hld/bin:"$PATH
# Add Quartus SOPC Builder to path
export PATH=$ALTERAROOT"/quartus/sopc_builder/bin:"$PATH

echo "Environment configured for Altera OpenCL"
