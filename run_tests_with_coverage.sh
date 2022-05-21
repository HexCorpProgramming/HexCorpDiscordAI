# due to imports leading to annotations being processed,
# we need to execute tests in isolation or they pollute each others contexts

for test_file in test/test_*.py
do
    echo "Running $test_file"
    python -m coverage run --parallel-mode --source=. --omit=test/*,env/* -m unittest "$test_file"
done
python -m coverage combine