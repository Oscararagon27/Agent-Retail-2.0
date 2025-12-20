# Serverless AI Data Analyst: Modern Data Lake Architecture (v2.0)

[![AWS: Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)]() 
[![AWS: Athena](https://img.shields.io/badge/AWS-Athena-blue.svg)]()

Este proyecto presenta la evolución de un Agente de IA para Inventarios. Originalmente basado en DynamoDB, el sistema ha sido migrado a una arquitectura de **Data Lake Moderno**, permitiendo análisis predictivo y consultas complejas sobre Big Data mediante lenguaje natural.

## 🏗️ Arquitectura del Sistema
El flujo integra servicios de AWS para desacoplar el almacenamiento del cómputo:
1. **Amazon S3**: Almacenamiento de archivos CSV (Dataset Superstore).
2. **AWS Glue**: Catálogo de datos y gestión de metadatos.
3. **Amazon Bedrock (Claude 3 Haiku)**: IA que traduce lenguaje natural a consultas SQL (Presto SQL).
4. **Amazon Athena**: Motor de consultas serverless que ejecuta el SQL directamente sobre S3.

## 📁 Estructura del Repositorio
- `src/agent.py`: Orquestador de IA y ejecución en Athena.
- `src/requirements.txt`: Dependencias optimizadas (Boto3).
- `template.yaml`: Infraestructura como Código (AWS SAM).

## 🚀 Despliegue Profesional
```bash
sam build
sam deploy --stack-name agente-retail-v3 --capabilities CAPABILITY_IAM --region us-east-1