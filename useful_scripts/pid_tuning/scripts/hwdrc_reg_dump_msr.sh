source hwdrc_osmailbox_config.inc.sh

echo "dump the Socket0 HWDRC settings "
core_id=1

hwdrc_reg_dump

echo "dump the Socket1 HWDRC settings "
core_id=33

hwdrc_reg_dump
