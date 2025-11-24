FROM amazon/aws-lambda-python:3.13-arm64

WORKDIR /var/task

COPY requirements.txt  .

RUN pip install -r requirements.txt

COPY --chown=root:root  lambda_function.py ${LAMBDA_TASK_ROOT}

RUN chmod 755 ${LAMBDA_TASK_ROOT}/lambda_function.py

CMD ["lambda_function.lambda_handler"]
