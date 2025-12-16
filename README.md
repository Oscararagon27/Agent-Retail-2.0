# 🏷️ Agente IA de Inventario Retail (Bedrock + SAM + DynamoDB)

Este proyecto implementa un agente de inteligencia artificial conversacional sin servidor (Serverless) en AWS. El agente utiliza **Claude 3 Haiku** para activar herramientas de función (*Tool Use*) y consultar el stock de productos en una base de datos DynamoDB.

## 🏗️ Arquitectura del Sistema

El flujo de trabajo sigue el patrón de Agente y Herramienta (Tool Use):

1. **Usuario** envía la pregunta (e.g., "Stock de Electrónica") a la API Gateway.
2. **Lambda Agent (`agent.py`)** envía el prompt y la definición de la herramienta a Bedrock.
3. **Bedrock (Claude 3 Haiku)** detecta la necesidad de la herramienta (`query_inventory`) y devuelve una llamada a la función.
4. La **Lambda** ejecuta la función Python `query_dynamodb`.
5. `query_dynamodb` realiza un **SCAN** a DynamoDB (se usa scan para evitar problemas con el GSI).
6. Los resultados de los datos (`Tool Result`) se envían de vuelta a Bedrock.
7. **Claude 3 Haiku** genera la respuesta final conversacional.

## 📁 Estructura del Proyecto

retail-agent-backend/ ├── template.yaml # Define la infraestructura (Lambda, DynamoDB, API Gateway, IAM) ├── src/ │ ├── agent.py # Lógica principal, Tool Definition, Bedrock calls. │ └── load_data.py # Función para cargar datos iniciales de prueba. ├── requirements.txt # Dependencias de Python. └── README.md # Documentación del proyecto.


## 🚀 Despliegue y Uso

### 1. Requisitos

* AWS CLI y AWS SAM CLI instalados y configurados.
* Acceso a los modelos **Claude 3 Haiku** en AWS Bedrock.

### 2. Despliegue

```bash
# 1. Instalar dependencias
sam build

# 2. Desplegar la infraestructura (Asegúrate de reemplazar el nombre del bucket de S3)
sam deploy \
    --stack-name retail-agent-backend \
    --s3-bucket [TU_BUCKET_DE_ARTEFACTOS] \
    --region us-east-1 \
    --capabilities CAPABILITY_IAM \
    --no-confirm-changeset