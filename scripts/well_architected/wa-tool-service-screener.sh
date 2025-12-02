cd /tmp
python3 -m venv .
source bin/activate
python3 -m pip install --upgrade pip
rm -rf service-screener-v2
git clone https://github.com/aws-samples/service-screener-v2.git
cd service-screener-v2
pip install -r requirements.txt
python3 unzip_botocore_lambda_runtime.py
alias screener='python3 $(pwd)/main.py'