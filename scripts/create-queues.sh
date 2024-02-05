# wrapper for test-queues.py

echo "Input received: ARGC:$# ARGV[1]: $1"

# read the input file
input_file=$1
echo "Input file: $input_file"

# strip .csv extension and add .yaml
cfg_file="${input_file%.*}.yaml"
echo "Config file: $cfg_file"

# run the test-queues.py
python create-queues.py --input $input_file --config $cfg_file --verbose
