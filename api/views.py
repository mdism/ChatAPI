import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import exception_handler
from django.core.cache import cache
from ollama import chat
from django.conf import settings
import os


def read_system_promt(path:str):
    BASE_DIR = settings.BASE_DIR
    filepath = os.path.join(BASE_DIR, path)
    if not os.path.exists(filepath):
        return {}
    else:
        with open(filepath, "r") as file:
            system_prompt = file.read()
            return system_prompt



class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication
    throttle_classes = [UserRateThrottle]  # Apply rate limiting

    def post(self, request, *args, **kwargs):
        try:
            # Extract data from the request
            text = request.data.get('text')
            conversation_id = request.data.get('conversation_id', 'default')

            # Fetch conversation history from Redis
            conversation_key = f"conversation:{conversation_id}"
            conversation_history = cache.get(conversation_key, [])

            # Initialize conversation history if empty
            if not conversation_history:
                conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]

            # Append user message to conversation history
            conversation_history.append({"role": "user", "content": text})

            # Call the Ollama chat model
            response = chat(model="qwen2.5:3b", messages=conversation_history)
            result = response['message']['content']

            # Remove <think> tags
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()

            # Append assistant message to conversation history
            conversation_history.append({"role": "assistant", "content": result})

            # Save updated conversation history back to Redis
            cache.set(conversation_key, conversation_history, timeout=None)  # No expiration

            # Return the result
            return Response({
                'result': result,
                'conversation_id': conversation_id
            })
       
        except Exception as e:
            # Log the error and return a 500 response
            print(f"Error occurred: {str(e)}")
            return Response({'error': str(e)}, status=500)

# import uuid

# def get_conversation_id():
#     id = uuid.uuid4()
#     print(f"{id=}")
#     return uuid.uuid4()


class ChatAPISystemView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication
    throttle_classes = [UserRateThrottle]  # Apply rate limiting
    def get(self, request, *args, **kwargs):
        result =  read_system_promt('./SYSTEM_PROMPT')
        conversation_id = 1122
        return Response({
                'result': result,
                'conversation_id': conversation_id
            })

    def post(self, request, *args, **kwargs):
        try:
            # Extract data from the request
            text = request.data.get('text')
            conversation_id = request.data.get('conversation_id', 'default')
            print(conversation_id)

            if not text:
                return Response({'error': 'The "text" field is required.'}, status=400)

            # Fetch conversation history from Redis
            conversation_key = f"conversation:{conversation_id}"
            conversation_history = cache.get(conversation_key, [])
            SYSTEM_PROMPT =  read_system_promt('./SYSTEM_PROMPT')
            # Initialize conversation history if empty
            if not conversation_history:
                conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Append user message to conversation history
            conversation_history.append({"role": "user", "content": text})

            # Call the Ollama chat model
            response = chat(model="qwen2.5:3b", messages=conversation_history)
            result = response['message']['content']

            # Remove <think> tags
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()

            # Append assistant message to conversation history
            conversation_history.append({"role": "assistant", "content": result})

            # Save updated conversation history back to Redis
            cache.set(conversation_key, conversation_history, timeout=None)  # No expiration

            # Return the result
            return Response({
                'result': result,
                'conversation_id': conversation_id
            })
       
        except Exception as e:
            # Log the error and return a 500 response
            print(f"Error occurred: {str(e)}")
            return Response({'error': str(e)}, status=500)
        
