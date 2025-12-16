import json
import boto3
import os
import traceback
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')

TABLE_NAME = os.environ['INVENTORY_TABLE']
table = dynamodb.Table(TABLE_NAME)

# Función para consultar DynamoDB
def query_dynamodb(query_params):
    """Query DynamoDB by category using SCAN with filter"""
    try:
        category = query_params.get('category', '').strip()
        
        if not category:
            return json.dumps({"error": "No category specified"})
        
        print(f"[QUERY_DYNAMODB] Original search category: '{category}'")
        
        # Mapeo de categorías (inglés -> español y variantes)
        category_mapping = {
            "electronics": ["Electrónica", "Electr¥nica", "Electronica", "electronics"],
            "electrónica": ["Electrónica", "Electr¥nica", "Electronica"],
            "electronica": ["Electrónica", "Electr¥nica", "Electronica"],
            "hogar": ["Hogar", "Home", "hogar"],
            "hogan": ["Hogar"],  # Corrección de error común de Claude
            "ropa": ["Ropa", "Clothing", "Clothes", "ropa"],
            "clothing": ["Ropa", "Clothing", "Clothes"],
            "home": ["Hogar", "Home", "hogar"]
        }
        
        # Determinar qué categorías buscar
        search_categories = [category]
        
        # Añadir mapeo si existe
        lower_category = category.lower()
        if lower_category in category_mapping:
            search_categories.extend(category_mapping[lower_category])
        
        # También añadir variantes comunes
        if "electron" in lower_category:
            search_categories.extend(["Electrónica", "Electr¥nica", "Electronica", "Electronics"])
        
        # Eliminar duplicados
        search_categories = list(dict.fromkeys(search_categories))
        
        print(f"[QUERY_DYNAMODB] Will search for categories: {search_categories}")
        
        items_found = []
        matched_category = category
        
        # Buscar en todas las categorías posibles
        for cat in search_categories:
            if not cat:  # Skip empty
                continue
                
            try:
                print(f"[QUERY_DYNAMODB] Trying category: '{cat}'")
                response = table.scan(
                    FilterExpression=Attr('category').eq(cat),
                    Limit=100
                )
                
                items = response.get('Items', [])
                if items:
                    items_found = items
                    matched_category = cat
                    print(f"[QUERY_DYNAMODB] Found {len(items)} items with category '{cat}'")
                    break
                else:
                    print(f"[QUERY_DYNAMODB] No items found for category '{cat}'")
            except Exception as scan_error:
                print(f"[QUERY_DYNAMODB] Error scanning for '{cat}': {scan_error}")
                continue
        
        # Si no encontramos nada, hacer un scan completo para ver qué hay
        if not items_found:
            print(f"[QUERY_DYNAMODB] No items found for any category variant")
            
            try:
                # Hacer un scan completo para diagnóstico
                full_scan = table.scan(Limit=20)
                all_items = full_scan.get('Items', [])
                
                # Extraer categorías únicas
                unique_categories = set()
                for item in all_items:
                    if 'category' in item:
                        cat_value = item['category']
                        # Limpiar el valor si es un dict (formato DynamoDB)
                        if isinstance(cat_value, dict) and 'S' in cat_value:
                            cat_value = cat_value['S']
                        elif isinstance(cat_value, str):
                            cat_value = cat_value
                        else:
                            cat_value = str(cat_value)
                        unique_categories.add(cat_value)
                
                print(f"[QUERY_DYNAMODB] Available categories in DB: {list(unique_categories)}")
                
                return json.dumps({
                    "count": 0,
                    "searched_for": category,
                    "available_categories": list(unique_categories),
                    "message": f"No products found for '{category}'. Available categories: {list(unique_categories)}"
                })
                
            except Exception as e:
                print(f"[QUERY_DYNAMODB] Error in full scan: {e}")
                return json.dumps({
                    "count": 0,
                    "searched_for": category,
                    "message": f"No products found for '{category}' and could not scan table"
                })
        
        # Procesar items encontrados
        total_stock = 0
        product_names = []
        
        for item in items_found:
            # Extraer valores (manejar formato DynamoDB)
            item_name = item.get('name', 'Unknown')
            if isinstance(item_name, dict) and 'S' in item_name:
                item_name = item_name['S']
            elif isinstance(item_name, str):
                item_name = item_name
            
            item_category = item.get('category', 'Unknown')
            if isinstance(item_category, dict) and 'S' in item_category:
                item_category = item_category['S']
            elif isinstance(item_category, str):
                item_category = item_category
            
            stock = item.get('stock_quantity', 0)
            if isinstance(stock, dict) and 'N' in stock:
                try:
                    stock = float(stock['N'])
                except:
                    stock = 0
            elif isinstance(stock, Decimal):
                stock = float(stock)
            elif isinstance(stock, (int, float)):
                stock = float(stock)
            else:
                stock = 0
            
            total_stock += stock
            product_names.append(str(item_name))
        
        # Crear respuesta estructurada
        result = {
            "count": len(items_found),
            "category": matched_category,
            "total_stock": total_stock,
            "product_count": len(items_found),
            "product_names": product_names[:10],
            "message": f"Found {len(items_found)} products in category '{matched_category}' with total stock of {total_stock} units."
        }
        
        if product_names:
            result["message"] += f" Products include: {', '.join(product_names[:3])}"
        
        print(f"[QUERY_DYNAMODB] Final result: {result}")
        # ¡IMPORTANTE: JSON válido con ensure_ascii=False para caracteres españoles!
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        print(f"[QUERY_DYNAMODB ERROR] {str(e)}")
        traceback.print_exc()
        return json.dumps({"error": str(e)})

def lambda_handler(event, context):
    try:
        print("=== LAMBDA_HANDLER START ===")
        print(f"[EVENT] {json.dumps(event, default=str)}")
        
        # 1. Extract user question
        body = json.loads(event.get('body', '{}'))
        user_prompt = body.get('prompt', 'Productos de Hogar')
        print(f"[PROMPT] User: '{user_prompt}'")
        
        # 2. Define Tools for Bedrock (EN ESPAÑOL)
        tools = [
            {
                "toolSpec": {
                    "name": "query_inventory",
                    "description": "Busca productos en el inventario por categoría específica como Electrónica, Ropa, Hogar, Deportes, Juguetes, etc.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "category": {
                                    "type": "string",
                                    "description": "La categoría del producto a buscar (ej: 'Electrónica', 'Ropa', 'Hogar')"
                                }
                            },
                            "required": ["category"]
                        }
                    }
                }
            }
        ]
        
        # 3. System prompt (MEJORADO - instrucciones claras)
        system_prompt = """Eres un asistente de inventario retail en español. Sigue ESTOS pasos:

1. SIEMPRE usa 'query_inventory' cuando te pregunten sobre productos o stock
2. Extrae SOLO UNA de estas categorías EXACTAS:
   - Si dice "Hogar" -> category="Hogar" (¡con R!)
   - Si dice "Electrónica" -> category="Electrónica"
   - Si dice "Ropa" -> category="Ropa"
   - Cualquier otra cosa -> category="Hogar"

3. Espera los resultados de la herramienta
4. Cuando recibas los datos JSON del toolResult, ANALÍZALOS y:
   - Di cuántos productos hay en esa categoría
   - Di el stock total de todos los productos
   - Menciona algunos nombres de productos
   - Responde en español amigable y útil

EJEMPLO de respuesta CORRECTA:
"En la categoría Hogar hay 2 productos con un stock total de 30 unidades. Los productos incluyen: Libro Cocina y Mesa Auxiliar."

IMPORTANTE: 
- ¡"Hogar" se escribe con R, no "Hogan"!
- Cuando veas los datos del toolResult, DEBES responder al usuario."""
        
        messages = [{"role": "user", "content": [{"text": user_prompt}]}]
        
        # 4. Initial diagnostics
        print(f"[TOOLS] Tool defined: {tools[0]['toolSpec']['name']}")
        print(f"[SYSTEM_PROMPT] First 300 chars: {system_prompt[:300]}...")
        
        # 5. First call to Bedrock
        print("[BEDROCK] First call...")
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig={"tools": tools},
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 0.1,  # Baja temperatura para comportamiento determinista
                "topP": 0.9
            }
        )
        
        # 6. Detailed diagnostics
        print("=== BEDROCK RESPONSE (1st call) ===")
        response_json = json.dumps(response, default=str)
        print(f"Response: {response_json[:500]}...")
        
        # 7. Look for toolUse in the correct structure
        output_message = response.get('output', {}).get('message', {})
        output_content = output_message.get('content', [])
        
        print(f"[OUTPUT_CONTENT] Length: {len(output_content)}")
        
        tool_use_item = None
        for i, content_item in enumerate(output_content):
            if content_item:
                item_keys = list(content_item.keys())
                print(f"[CONTENT_ITEM {i}] Keys: {item_keys}")
                
                if 'toolUse' in content_item:
                    tool_use_item = content_item['toolUse']
                    print(f"[TOOLUSE_FOUND] Index {i}: {tool_use_item.get('name')}")
                    break
                elif 'text' in content_item:
                    text_content = content_item.get('text', '')
                    print(f"[TEXT_RESPONSE {i}] First 100 chars: {text_content[:100]}...")
        
        if tool_use_item:
            print(f"[TOOLUSE_DETAILS] Name: {tool_use_item.get('name')}")
            print(f"[TOOLUSE_DETAILS] Input: {tool_use_item.get('input')}")
            
            if tool_use_item.get('name') == 'query_inventory':
                # Execute the tool
                query_params = tool_use_item.get('input', {})
                print(f"[TOOL_INPUT] Parameters: {query_params}")
                
                tool_output = query_dynamodb(query_params)
                print(f"[TOOL_OUTPUT] First 500 chars: {tool_output[:500]}...")
                
                # Prepare messages for second call
                messages.append({
                    "role": "assistant",
                    "content": [{"toolUse": tool_use_item}]
                })
                
                messages.append({
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": tool_use_item['toolUseId'],
                            "content": [{"text": tool_output}]
                        }
                    }]
                })
                
                # SEGUNDA LLAMADA CORREGIDA (con system prompt)
                print("[BEDROCK] Second call with tool results...")
                final_response = bedrock.converse(
                    modelId="anthropic.claude-3-haiku-20240307-v1:0",
                    messages=messages,
                    system=[{"text": system_prompt}],  # ¡CRÍTICO: system prompt en segunda llamada!
                    toolConfig={"tools": tools},
                    inferenceConfig={
                        "maxTokens": 1024,
                        "temperature": 0.1
                    }
                )
                
                print("=== FINAL BEDROCK RESPONSE ===")
                final_json = json.dumps(final_response, default=str, indent=2)
                print(final_json)
                
                # Diagnóstico detallado
                print("=== DIAGNÓSTICO FINAL ===")
                print(f"Final response type: {type(final_response)}")
                print(f"Final response keys: {final_response.keys() if isinstance(final_response, dict) else 'Not a dict'}")
                
                final_output = final_response.get('output', {})
                print(f"Final output keys: {final_output.keys()}")
                
                final_message = final_output.get('message', {})
                print(f"Final message keys: {final_message.keys()}")
                
                final_content = final_message.get('content', [])
                print(f"Final content length: {len(final_content)}")
                
                # Buscar texto en la respuesta
                final_text = 'No se pudo generar la respuesta final.'
                for content_item in final_content:
                    if content_item and 'text' in content_item:
                        final_text = content_item['text']
                        break
                
                print(f"[FINAL_RESPONSE] Text: {final_text}")
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'response': final_text})
                }
            else:
                print(f"[ERROR] Unknown tool name: {tool_use_item.get('name')}")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'response': f'Herramienta desconocida: {tool_use_item.get("name")}'})
                }
        else:
            print("[WARNING] No toolUse found in response!")
            
            # Check for direct text response
            for content_item in output_content:
                if content_item and 'text' in content_item:
                    direct_text = content_item['text']
                    print(f"[DIRECT_RESPONSE] Claude responded directly: {direct_text[:200]}...")
                    
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'response': direct_text})
                    }
        
        # Fallback
        fallback_text = output_message.get('text', 'No se pudo generar una respuesta.')
        print(f"[FALLBACK] Using fallback: {fallback_text}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'response': fallback_text})
        }
        
    except Exception as e:
        print(f"[CRITICAL_ERROR] {str(e)}")
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'message': 'Error interno del agente de IA',
                'stack': traceback.format_exc()
            })
        }