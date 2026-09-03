# ==============================================================================
# FinGraph Apache Flink Stream Processing Container
# ==============================================================================
FROM flink:1.18.1-scala_2.12-java11

# Install Python 3, pip, and build tools
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-dev \
      build-essential \
      wget && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# Download Kafka connector jar into Flink lib directory
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.1.0-1.18/flink-sql-connector-kafka-3.1.0-1.18.jar

WORKDIR /opt/fingraph

# Install Python streaming dependencies
COPY flink/requirements.txt /opt/fingraph/flink/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/fingraph/flink/requirements.txt

# Copy application source code
COPY . /opt/fingraph/

ENV PYTHONPATH=/opt/fingraph

CMD ["python", "flink/src/job.py"]
