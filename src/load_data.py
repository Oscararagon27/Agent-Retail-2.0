import json
import boto3
import os
import csv
from io import StringIO
from decimal import Decimal

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Obtener nombre de la tabla desde la variable de entorno
TABLE_NAME = os.environ['INVENTORY_TABLE']
table = dynamodb.Table(TABLE_NAME)

# Datos de inventario simulados (incrustados en la Lambda)
SAMPLE_DATA_CSV = """
product_id,name,category,price,stock_quantity
P001,Laptop Ultra,Electrónica,1200.50,5
P002,Smartphone Pro,Electrónica,850.00,12
P003,Smart TV 55,Electrónica,799.99,3
P004,Camiseta Algodón,Ropa,19.99,150
P005,Pantalón Jeans,Ropa,45.00,80
P006,Libro Cocina,Hogar,25.50,20
P007,Mesa Auxiliar,Hogar,150.00,10
P008,Auriculares BT,Electrónica,89.99,35
"""

def batch_write_data(items):
    """Escribe los ítems en DynamoDB usando batch_writer."""
    count = 0
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
            count += 1
    return count

def parse_csv_data(csv_data):
    """Convierte datos CSV a una lista de diccionarios para DynamoDB, limpiando los encabezados."""
    items = []
    csvfile = StringIO(csv_data.strip()) # Limpiamos espacios en blanco externos del string
    
    # Usamos DictReader y luego ajustamos las claves
    reader = csv.DictReader(csvfile)
    
    # 1. Creamos un mapeo de nombres de columna limpiados
    fieldnames = [name.strip() for name in reader.fieldnames]
    
    for row in reader:
        # 2. Crea un nuevo diccionario con claves limpias para evitar KeyError
        # Creamos una lista de (clave limpia, valor)
        cleaned_row = {fieldnames[i]: val for i, (key, val) in enumerate(row.items())}
        
        # 3. Convertir tipos de datos usando las claves limpias
        item = {
            'product_id': cleaned_row['product_id'],
            'name': cleaned_row['name'],
            'category': cleaned_row['category'],
            # Usar Decimal para números en DynamoDB
            'price': Decimal(str(cleaned_row['price'])),
            'stock_quantity': int(cleaned_row['stock_quantity']),
        }
        items.append(item)
    return items

def lambda_handler(event, context):
    try:
        # 1. Parsear el dataset
        items_to_load = parse_csv_data(SAMPLE_DATA_CSV)
        
        # 2. Cargar los datos a DynamoDB
        count = batch_write_data(items_to_load)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Datos cargados exitosamente. {count} items escritos en la tabla {TABLE_NAME}.'
            })
        }
    
    except Exception as e:
        # Manejo de error único (se eliminó el bloque duplicado)
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'message': 'Ocurrió un error al cargar los datos.'})
        }