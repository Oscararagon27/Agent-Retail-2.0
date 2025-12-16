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

Esta es la estructura de archivos del proyecto serverless:

| Archivo/Directorio | Propósito |
| :--- | :--- |
| **`retail-agent-backend/`** | Directorio raíz del proyecto Serverless. |
| **`template.yaml`** | Define la infraestructura completa (SAM/CloudFormation): Lambdas, DynamoDB, API Gateway, y permisos IAM. |
| **`src/`** | Contiene el código fuente de las funciones Lambda. |
| `src/agent.py` | Lógica principal del agente: gestión de la API de Bedrock y el flujo de Tool Use. |
| `src/load_data.py` | Función de utilidad para cargar datos iniciales de inventario en DynamoDB. |
| **`requirements.txt`** | Dependencias de Python (`boto3`, etc.) necesarias para las funciones Lambda. |
| **`README.md`** | Documentación del proyecto. |


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