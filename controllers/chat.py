from flask import render_template, request, jsonify, session
from flask_login import current_user, login_required
from models.chat import save_user_chat_history
from controllers.ai_analysis import extract_structured_data
from datetime import datetime
from utils.logger import chat_logger, ai_logger, log_function_call, log_user_action, log_error, log_ai_activity
import secrets
import time


def extract_text_from_llm_response(response):
    """Extract text from LLMResponse object or return as string"""
    if hasattr(response, 'content'):
        return response.content
    elif hasattr(response, 'text'):
        return response.text
    elif not isinstance(response, str):
        return str(response)
    return response


@log_function_call(chat_logger)
def chatbot():
    """Chatbot interface - advanced AI copilot chatbot"""
    try:
        from config import get_company_config
        company_config = get_company_config(current_user.company_id)
        company_name = company_config.full_name
        chat_logger.info(f"Chatbot interface accessed by user {current_user.username} for company {company_name}")
    except Exception as e:
        company_name = current_user.company_id.title()
        log_error(e, f"Failed to get company config for {current_user.company_id}")
    
    log_user_action("Chatbot Access", current_user.id, f"Interface: Basic, Company: {company_name}")
    
    return render_template("chatbot_advanced.html", 
                         company_name=company_name,
                         user=current_user)


@log_function_call(chat_logger)
def chatbot_advanced():
    """Advanced AI copilot chatbot interface"""
    from config import get_company_config
    
    try:
        company_config = get_company_config(current_user.company_id)
        company_name = company_config.full_name
        company_display = company_config.name  # Fix: use name instead of display_name
        selected_company = current_user.company_id  # Add selected_company for template
        chat_logger.info(f"Advanced chatbot interface accessed by user {current_user.username} for company {company_name}")
    except Exception as e:
        company_config = None  # Set to None when config fails to load
        company_name = current_user.company_id.title()
        company_display = current_user.company_id.title()
        selected_company = current_user.company_id
        log_error(e, f"Failed to get company config for {current_user.company_id}")
    
    log_user_action("Chatbot Access", current_user.id, f"Interface: Advanced, Company: {company_name}")
    
    return render_template("chatbot_advanced.html", 
                         company_name=company_name,
                         company_display=company_display,
                         user_company=current_user.company_id,
                         selected_company=selected_company,  # Add selected_company
                         company_config=company_config,      # Add company_config
                         user=current_user)


@log_function_call(chat_logger, log_args=False)  # Don't log full query content
def chatbot_query_stream():
    """Process chatbot queries with streaming responses"""
    from flask import Response
    import json
    
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            def auth_error():
                yield f"data: {json.dumps({'content': 'Please log in to use the chatbot.', 'done': True, 'error': 'authentication_required'})}\n\n"
            return Response(auth_error(), mimetype='text/event-stream')
        
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = (data.get("mode") or "pakwheels").strip().lower()
        thinking_mode = data.get("thinking", False)
        
        chat_logger.info(f"Streaming chat query from user {current_user.username}: mode={mode}, thinking={thinking_mode}")
        
        if not query:
            def empty_response():
                if mode == "insights":
                    yield f"data: {json.dumps({'content': 'Hello! How can I help you today?', 'done': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'content': 'Please ask something about your vehicle, concerns, or the available data.', 'done': True})}\n\n"
            return Response(empty_response(), mimetype='text/event-stream')
        
        # Get user's company
        user_company = current_user.company_id or 'haval'
        
        # Get or create session ID
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['chat_session_id'] = session_id
        
        def generate_response():
            try:
                # Handle Insights mode with streaming
                if mode == "insights":
                    import app
                    openai_client = app.get_openai_client()
                    if not openai_client:
                        yield f"data: {json.dumps({'content': 'Insights mode is not available.', 'done': True})}\n\n"
                        return
                    
                    try:
                        from models.chat import get_user_chat_history
                        history = get_user_chat_history(current_user.id, mode, session_id)
                        
                        messages = [{"role": "system", "content": "You are ChatGPT, a helpful AI assistant."}]
                        
                        if history:
                            for msg in history[-20:]:
                                if msg.get('role') in ['user', 'assistant']:
                                    content = msg['content'].strip()
                                    if content:
                                        messages.append({"role": msg['role'], "content": content})
                        
                        messages.append({"role": "user", "content": query})
                        
                        # Check if this is a GrokClient or actual OpenAI client
                        if hasattr(openai_client, 'chat') and hasattr(openai_client.chat, 'completions'):
                            # This is an actual OpenAI client with streaming support
                            response = openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages,
                                max_tokens=2000,
                                temperature=0.7,
                                stream=True
                            )
                            
                            full_answer = ""
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    full_answer += content
                                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        else:
                            # This is a GrokClient, use generate method and simulate streaming
                            prompt_parts = []
                            for msg in messages:
                                if msg['role'] == 'system':
                                    prompt_parts.append(f"System: {msg['content']}")
                                elif msg['role'] == 'user':
                                    prompt_parts.append(f"User: {msg['content']}")
                                elif msg['role'] == 'assistant':
                                    prompt_parts.append(f"Assistant: {msg['content']}")
                            
                            prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
                            llm_response = openai_client.generate(prompt, max_tokens=2000, temperature=0.7)
                            full_answer = extract_text_from_llm_response(llm_response)
                            
                            # Simulate streaming by sending words in chunks
                            words = full_answer.split()
                            chunk_size = 8
                            for i in range(0, len(words), chunk_size):
                                chunk = " ".join(words[i:i+chunk_size])
                                if i + chunk_size < len(words):
                                    chunk += " "
                                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                        
                        save_user_chat_history(current_user.id, session_id, mode, query, full_answer)
                        structured_data = extract_structured_data(full_answer, None, mode)
                        
                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"
                        
                    except Exception as e:
                        log_error(e, f"OpenAI streaming error")
                        yield f"data: {json.dumps({'content': 'Sorry, there was an error.', 'done': True})}\n\n"
                
                elif mode == "dealership":
                    # Dealership Database Mode - LLM-powered SQL queries
                    try:
                        from ai.dealership_engine import DealershipPipeline
                        from models.chat import get_user_chat_history

                        # Initialize dealership pipeline
                        dealership_pipeline = DealershipPipeline()

                        # Get chat history (already uses existing intent classifier for follow-ups)
                        history = get_user_chat_history(current_user.id, mode, session_id)
                        if len(history) == 0:
                            history = None

                        # Get answer from dealership pipeline
                        chat_logger.info(f"Dealership query from {current_user.username}: {query[:100]}")
                        answer = dealership_pipeline.answer(query, chat_history=history)

                        # Stream answer in chunks
                        words = answer.split()
                        chunk_size = 10
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                        # Save to chat history
                        save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        structured_data = extract_structured_data(answer, None, mode)

                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"

                    except Exception as e:
                        chat_logger.error(f"Dealership pipeline error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': f'Sorry, dealership query failed. Please try rephrasing your question.', 'done': True})}\n\n"

                elif mode == "facebook_beta":
                    # Facebook Beta Mode - Process Facebook group data with advanced filtering
                    try:
                        from services.ai_service import AIService

                        # Get answer from AI service Facebook query processor
                        chat_logger.info(f"Facebook Beta query from {current_user.username}: {query[:100]}")
                        answer = AIService.process_chat_query(query, mode, user_company)

                        # Stream answer in chunks
                        words = answer.split()
                        chunk_size = 10
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                        # Save to chat history
                        save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        structured_data = extract_structured_data(answer, None, mode)

                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"

                    except Exception as e:
                        chat_logger.error(f"Facebook Beta processing error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': f'Sorry, Facebook Beta query failed. Please try rephrasing your question.', 'done': True})}\n\n"
                        words = answer.split()
                        chunk_size = 10
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                        # Save to chat history
                        save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        structured_data = extract_structured_data(answer, None, mode)

                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"

                    except Exception as e:
                        chat_logger.error(f"Dealership pipeline error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': f'Sorry, dealership query failed. Please try rephrasing your question.', 'done': True})}\n\n"

                elif mode == "facebook_beta":
                    # Facebook Beta Mode - Process Facebook group data with advanced filtering
                    try:
                        from services.ai_service import AIService

                        # Get answer from AI service Facebook query processor
                        chat_logger.info(f"Facebook Beta query from {current_user.username}: {query[:100]}")
                        answer = AIService.process_chat_query(query, mode, user_company)

                        # Stream answer in chunks
                        words = answer.split()
                        chunk_size = 10
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                        # Save to chat history
                        save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        structured_data = extract_structured_data(answer, None, mode)

                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"

                    except Exception as e:
                        chat_logger.error(f"Facebook Beta processing error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': f'Sorry, Facebook Beta query failed. Please try rephrasing your question.', 'done': True})}\n\n"

                else:
                    # RAG-based modes (PakWheels, WhatsApp)
                    try:
                        from ai.haval_pipeline import get_rag_engine
                        rag = get_rag_engine(company_id=user_company)

                        if rag is None:
                            yield f"data: {json.dumps({'content': 'The AI system is not ready.', 'done': True})}\n\n"
                            return

                        from models.chat import get_user_chat_history
                        history = get_user_chat_history(current_user.id, mode, session_id)
                        if len(history) == 0:
                            history = None

                        answer = rag.answer(query, history=history, thinking_mode=thinking_mode, source=mode)
                        
                        # Stream answer in chunks
                        words = answer.split()
                        chunk_size = 10  # Larger chunks for faster streaming
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                            # No delay for maximum speed
                        
                        save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        structured_data = extract_structured_data(answer, None, mode)
                        
                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"
                        
                    except Exception as e:
                        log_error(e, f"RAG streaming error")
                        yield f"data: {json.dumps({'content': 'Sorry, there was an error.', 'done': True})}\n\n"
                    
            except Exception as e:
                log_error(e, f"Streaming error")
                yield f"data: {json.dumps({'content': 'Sorry, I encountered an error.', 'done': True})}\n\n"
        
        return Response(generate_response(), mimetype='text/event-stream')
        
    except Exception as e:
        log_error(e, f"Request processing error")
        def error_response():
            yield f"data: {json.dumps({'content': 'Sorry, I could not generate a response.', 'done': True})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')


@log_function_call(chat_logger, log_args=False)  # Don't log full query content
def chatbot_query_fast():
    """Super fast chatbot query with minimal processing and immediate streaming"""
    from flask import Response
    import json
    
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = (data.get("mode") or "pakwheels").strip().lower()
        thinking_mode = False  # Force non-thinking mode for speed
        
        chat_logger.info(f"Fast chat query from user {current_user.username}: mode={mode}")
        
        if not query:
            def empty_response():
                if mode == "insights":
                    yield f"data: {json.dumps({'content': 'Hello! How can I help you today?', 'done': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'content': 'Please ask something about your vehicle, concerns, or the available data.', 'done': True})}\n\n"
            return Response(empty_response(), mimetype='text/event-stream')
        
        # Get user's company
        user_company = current_user.company_id or 'haval'
        
        # Get or create session ID
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['chat_session_id'] = session_id
        
        def generate_fast_response():
            try:
                start_time = time.time()
                
                # Handle Insights mode with streaming
                if mode == "insights":
                    import app
                    openai_client = app.get_openai_client()
                    if not openai_client:
                        yield f"data: {json.dumps({'content': 'Insights mode is not available. OpenAI integration is required.', 'done': True})}\n\n"
                        return
                    
                    try:
                        # Minimal history for speed (only last 4 messages)
                        from models.chat import get_user_chat_history
                        history = get_user_chat_history(current_user.id, mode, session_id, limit=4)
                        
                        # Build minimal messages for speed
                        messages = [
                            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise responses."}
                        ]
                        
                        if history:
                            for msg in history[-4:]:  # Only last 4 messages for speed
                                if msg.get('role') in ['user', 'assistant']:
                                    content = msg['content'].strip()
                                    if content:
                                        messages.append({"role": msg['role'], "content": content})
                        
                        messages.append({"role": "user", "content": query})
                        
                        # Check if this is a GrokClient or actual OpenAI client
                        if hasattr(openai_client, 'chat') and hasattr(openai_client.chat, 'completions'):
                            # This is an actual OpenAI client with streaming support
                            response = openai_client.chat.completions.create(
                                model="gpt-4o-mini",  # Use faster mini model
                                messages=messages,
                                max_tokens=1000,  # Reduced for speed
                                temperature=0.3,  # Lower for faster, more focused responses
                                stream=True
                            )
                            
                            full_answer = ""
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    full_answer += content
                                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        else:
                            # This is a GrokClient, use generate method and simulate streaming
                            prompt_parts = []
                            for msg in messages:
                                if msg['role'] == 'system':
                                    prompt_parts.append(f"System: {msg['content']}")
                                elif msg['role'] == 'user':
                                    prompt_parts.append(f"User: {msg['content']}")
                                elif msg['role'] == 'assistant':
                                    prompt_parts.append(f"Assistant: {msg['content']}")
                            
                            prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
                            llm_response = openai_client.generate(prompt, max_tokens=1000, temperature=0.3)
                            full_answer = extract_text_from_llm_response(llm_response)
                            
                            # Simulate streaming by sending words in chunks
                            words = full_answer.split()
                            chunk_size = 8
                            for i in range(0, len(words), chunk_size):
                                chunk = " ".join(words[i:i+chunk_size])
                                if i + chunk_size < len(words):
                                    chunk += " "
                                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                        
                        # Save to chat history (async to not block response)
                        try:
                            save_user_chat_history(current_user.id, session_id, mode, query, full_answer)
                        except:
                            pass  # Don't let saving block the response
                        
                        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        
                    except Exception as e:
                        log_error(e, f"Fast OpenAI streaming error for user {current_user.username}")
                        yield f"data: {json.dumps({'content': 'Sorry, there was an error. Please try again.', 'done': True})}\n\n"
                
                else:
                    # RAG-based modes with speed optimizations
                    try:
                        # Quick status check without detailed validation
                        from ai.haval_pipeline import get_rag_engine
                        rag = get_rag_engine(company_id=user_company)
                        
                        if rag is None:
                            yield f"data: {json.dumps({'content': 'The AI system is not ready yet. Please try again in a moment.', 'done': True})}\n\n"
                            return
                        
                        # Minimal history for speed
                        from models.chat import get_user_chat_history
                        history = get_user_chat_history(current_user.id, mode, session_id, limit=4)
                        if len(history) == 0:
                            history = None
                        
                        # Use RAG engine with speed optimizations
                        ai_start_time = time.time()
                        
                        # Force non-thinking mode and minimal processing
                        answer = rag.answer(query, history=history, thinking_mode=False, source=mode)
                        
                        # Stream the answer in chunks for immediate feedback
                        words = answer.split()
                        chunk_size = 8  # Larger chunks for faster streaming
                        
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                            # No delay for maximum speed
                        
                        # Save to chat history (async to not block response)
                        try:
                            save_user_chat_history(current_user.id, session_id, mode, query, answer)
                        except:
                            pass  # Don't let saving block the response
                        
                        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        
                    except Exception as e:
                        log_error(e, f"Fast RAG error for user {current_user.username}")
                        yield f"data: {json.dumps({'content': 'Sorry, there was an error processing your request.', 'done': True})}\n\n"
                    
            except Exception as e:
                log_error(e, f"Fast streaming error for user {current_user.username}")
                yield f"data: {json.dumps({'content': 'Sorry, I encountered an error.', 'done': True})}\n\n"
        
        return Response(generate_fast_response(), mimetype='text/event-stream')
        
    except Exception as e:
        log_error(e, f"Fast request processing error for user {current_user.username if current_user.is_authenticated else 'Anonymous'}")
        def error_response():
            yield f"data: {json.dumps({'content': 'Sorry, I could not generate a response.', 'done': True})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')
    """Process chatbot queries with streaming responses for super fast experience"""
    from flask import Response
    import json
    
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = (data.get("mode") or "pakwheels").strip().lower()
        thinking_mode = data.get("thinking", False)
        
        chat_logger.info(f"Streaming chat query from user {current_user.username}: mode={mode}, thinking={thinking_mode}")
        
        if not query:
            def empty_response():
                if mode == "insights":
                    yield f"data: {json.dumps({'content': 'Hello! How can I help you today?', 'done': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'content': 'Please ask something about your vehicle, concerns, or the available data.', 'done': True})}\n\n"
            return Response(empty_response(), mimetype='text/event-stream')
        
        # Get user's company
        user_company = current_user.company_id or 'haval'
        
        # Get or create session ID
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['chat_session_id'] = session_id
        
        def generate_response():
            try:
                start_time = time.time()
                
                # Handle Insights mode with streaming
                if mode == "insights":
                    import app
                    openai_client = app.get_openai_client()
                    if not openai_client:
                        yield f"data: {json.dumps({'content': 'Insights mode is not available. OpenAI integration is required.', 'done': True})}\n\n"
                        return
                    
                    try:
                        # Get chat history
                        from models.chat import get_user_chat_history
                        history = get_user_chat_history(current_user.id, mode, session_id)
                        
                        # Build messages
                        messages = [
                            {"role": "system", "content": "You are ChatGPT, a helpful AI assistant created by OpenAI. Provide clear, informative, and conversational responses. Be helpful, harmless, and honest."}
                        ]
                        
                        if history:
                            recent_history = history[-20:]
                            for msg in recent_history:
                                if msg.get('role') in ['user', 'assistant']:
                                    content = msg['content'].strip()
                                    if content:
                                        messages.append({"role": msg['role'], "content": content})
                        
                        messages.append({"role": "user", "content": query})
                        
                        # Check if this is a GrokClient or actual OpenAI client
                        ai_start_time = time.time()
                        if hasattr(openai_client, 'chat') and hasattr(openai_client.chat, 'completions'):
                            # This is an actual OpenAI client with streaming support
                            response = openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages,
                                max_tokens=2000,
                                temperature=0.7,
                                stream=True  # Enable streaming
                            )
                            
                            full_answer = ""
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    full_answer += content
                                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        else:
                            # This is a GrokClient, use generate method and simulate streaming
                            prompt_parts = []
                            for msg in messages:
                                if msg['role'] == 'system':
                                    prompt_parts.append(f"System: {msg['content']}")
                                elif msg['role'] == 'user':
                                    prompt_parts.append(f"User: {msg['content']}")
                                elif msg['role'] == 'assistant':
                                    prompt_parts.append(f"Assistant: {msg['content']}")
                            
                            prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
                            llm_response = openai_client.generate(prompt, max_tokens=2000, temperature=0.7)
                            full_answer = extract_text_from_llm_response(llm_response)
                            
                            # Simulate streaming by sending words in chunks
                            words = full_answer.split()
                            chunk_size = 8
                            for i in range(0, len(words), chunk_size):
                                chunk = " ".join(words[i:i+chunk_size])
                                if i + chunk_size < len(words):
                                    chunk += " "
                                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                        
                        ai_duration = time.time() - ai_start_time
                        
                        # Save to chat history
                        save_user_chat_history(current_user.id, session_id, mode, query, full_answer)
                        
                        # Extract structured data
                        structured_data = extract_structured_data(full_answer, None, mode)
                        
                        log_ai_activity("Insights Query", "OpenAI", None, ai_duration)
                        
                        yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"
                        
                    except Exception as e:
                        log_error(e, f"OpenAI streaming error for user {current_user.username}")
                        yield f"data: {json.dumps({'content': 'Sorry, the Insights mode encountered an error. Please try again.', 'done': True})}\n\n"
                
                else:
                    # RAG-based modes with optimized processing
                    try:
                        from ai.haval_pipeline import get_pipeline_status, get_rag_engine
                        status = get_pipeline_status()
                    except Exception as e:
                        yield f"data: {json.dumps({'content': 'The AI system is not available. Please try again later.', 'done': True})}\n\n"
                        return
                        
                    if status.get("status") != "ready":
                        status_msg = status.get("status", "unknown")
                        yield f"data: {json.dumps({'content': f'The insight engine is still processing (status: {status_msg}). Please wait until ready.', 'done': True})}\n\n"
                        return
                    
                    # Get company config and RAG engine
                    from config import get_company_config
                    company_config = get_company_config(user_company)
                    
                    # Validate source availability
                    if mode == "whatsapp" and not company_config.has_whatsapp:
                        company_name = company_config.name
                        yield f"data: {json.dumps({'content': f'WhatsApp data is not available for {company_name}. Please select PakWheels or Insights mode.', 'done': True})}\n\n"
                        return
                    elif mode == "pakwheels" and not company_config.has_pakwheels:
                        company_name = company_config.name
                        yield f"data: {json.dumps({'content': f'PakWheels data is not available for {company_name}. Please select a different data source.', 'done': True})}\n\n"
                        return
                    
                    try:
                        rag = get_rag_engine(company_id=user_company)
                    except Exception as e:
                        yield f"data: {json.dumps({'content': f'The {company_config.name} insight engine is not available yet.', 'done': True})}\n\n"
                        return
                        
                    if rag is None:
                        yield f"data: {json.dumps({'content': f'The {company_config.name} insight engine is not available yet.', 'done': True})}\n\n"
                        return
                    
                    # Get chat history
                    from models.chat import get_user_chat_history
                    history = get_user_chat_history(current_user.id, mode, session_id)
                    if len(history) == 0:
                        history = None
                    
                    # Use RAG engine with streaming if available
                    ai_start_time = time.time()
                    
                    # Check if RAG engine supports streaming
                    if hasattr(rag, 'answer_stream'):
                        # Stream from RAG engine
                        full_answer = ""
                        for chunk in rag.answer_stream(query, history=history, thinking_mode=thinking_mode, source=mode):
                            full_answer += chunk
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                    else:
                        # Fallback to regular answer but send immediately
                        answer = rag.answer(query, history=history, thinking_mode=thinking_mode, source=mode)
                        full_answer = answer
                        
                        # Send answer in chunks for perceived streaming
                        words = answer.split()
                        chunk_size = 10  # Larger chunks for faster streaming
                        for i in range(0, len(words), chunk_size):
                            chunk = " ".join(words[i:i+chunk_size])
                            if i + chunk_size < len(words):
                                chunk += " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                            # No delay for maximum speed
                    
                    ai_duration = time.time() - ai_start_time
                    
                    # Clean up any placeholder patterns
                    import re
                    full_answer = re.sub(r'CHART_PLACEHOLDER_\d+', '', full_answer)
                    full_answer = re.sub(r'__CHART_PLACEHOLDER_\d+__', '', full_answer)
                    full_answer = re.sub(r'\n\s*\n\s*\n', '\n\n', full_answer).strip()
                    
                    # Save to chat history
                    save_user_chat_history(current_user.id, session_id, mode, query, full_answer)
                    
                    # Extract structured data
                    structured_data = extract_structured_data(full_answer, None, mode)
                    
                    log_ai_activity(f"{mode.title()} Query", "RAG Engine", None, ai_duration)
                    
                    yield f"data: {json.dumps({'content': '', 'done': True, 'structured': structured_data})}\n\n"
                    
            except Exception as e:
                log_error(e, f"Streaming error for user {current_user.username}")
                yield f"data: {json.dumps({'content': 'Sorry, I encountered an error while processing your request.', 'done': True})}\n\n"
        
        return Response(generate_response(), mimetype='text/event-stream')
        
    except Exception as e:
        log_error(e, f"Request processing error for user {current_user.username if current_user.is_authenticated else 'Anonymous'}")
        def error_response():
            yield f"data: {json.dumps({'content': 'Sorry, I could not generate a response.', 'done': True})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')


@log_function_call(chat_logger, log_args=False)  # Don't log full query content
def chatbot_query():
    """Process chatbot queries with the RAG engine (legacy non-streaming endpoint)"""
    
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = (data.get("mode") or "pakwheels").strip().lower()
        thinking_mode = data.get("thinking", False)
        
        chat_logger.info(f"Chat query from user {current_user.username}: mode={mode}, thinking={thinking_mode}, query_length={len(query)}")
        
        if not query:
            if mode == "insights":
                return jsonify({"answer": "Hello! How can I help you today?"})
            else:
                return jsonify({
                    "answer": "Please ask something about your vehicle, concerns, or the available data."
                })
        
        # Get user's company
        user_company = current_user.company_id or 'haval'
        
        # Get or create session ID
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['chat_session_id'] = session_id
        
        start_time = time.time()
        
        try:
            # Handle Insights mode first (doesn't need RAG engine)
            if mode == "insights":
                chat_logger.info(f"Processing Insights query for user {current_user.username}")
                
                # Use OpenAI for insights mode
                import app
                openai_client = app.get_openai_client()
                if not openai_client:
                    return jsonify({
                        "answer": "Insights mode is not available. OpenAI integration is required."
                    })
                
                try:
                    # Get user-specific chat history for the mode
                    from models.chat import get_user_chat_history
                    history = get_user_chat_history(current_user.id, mode, session_id)
                    if len(history) == 0:
                        history = None
                    
                    # Build conversation history for ChatGPT-like experience
                    messages = [
                        {"role": "system", "content": "You are ChatGPT, a helpful AI assistant created by OpenAI. Provide clear, informative, and conversational responses. Be helpful, harmless, and honest. You can discuss a wide range of topics and help with various tasks."}
                    ]
                    
                    # Add conversation history (last 10 exchanges to stay within token limits)
                    if history:
                        recent_history = history[-20:]  # Last 20 messages (10 exchanges)
                        for msg in recent_history:
                            if msg.get('role') in ['user', 'assistant']:
                                # Clean the content from any placeholder patterns
                                content = msg['content']
                                import re
                                content = re.sub(r'CHART_PLACEHOLDER_\d+', '', content)
                                content = re.sub(r'__CHART_PLACEHOLDER_\d+__', '', content)
                                content = content.strip()
                                
                                if content:  # Only add non-empty messages
                                    messages.append({
                                        "role": msg['role'],
                                        "content": content
                                    })
                    
                    # Add current user message
                    messages.append({"role": "user", "content": query})
                    
                    ai_start_time = time.time()
                    
                    # Check if this is a GrokClient or actual OpenAI client
                    if hasattr(openai_client, 'chat') and hasattr(openai_client.chat, 'completions'):
                        # This is an actual OpenAI client
                        response = openai_client.chat.completions.create(
                            model="gpt-4o",  # Use latest GPT-4 model
                            messages=messages,
                            max_tokens=2000,
                            temperature=0.7,
                            presence_penalty=0.1,
                            frequency_penalty=0.1
                        )
                        answer = response.choices[0].message.content
                    else:
                        # This is a GrokClient or similar - it can handle messages array directly
                        llm_response = openai_client.generate(messages, max_tokens=2000, temperature=0.7)
                        # Extract text from LLMResponse object
                        answer = extract_text_from_llm_response(llm_response)
                    
                    ai_duration = time.time() - ai_start_time
                    
                    # Aggressive cleanup of any placeholder patterns
                    import re
                    answer = re.sub(r'CHART_PLACEHOLDER_\d+', '', answer)
                    answer = re.sub(r'__CHART_PLACEHOLDER_\d+__', '', answer)
                    answer = re.sub(r'\bCHART_PLACEHOLDER_\d+\b', '', answer)
                    answer = re.sub(r'CHART_PLACEHOLDER_\d+\s*', '', answer)
                    answer = re.sub(r'\s*CHART_PLACEHOLDER_\d+', '', answer)
                    answer = re.sub(r'\n\s*CHART_PLACEHOLDER_\d+\s*\n', '\n', answer)
                    answer = re.sub(r'^CHART_PLACEHOLDER_\d+\s*\n', '', answer, flags=re.MULTILINE)
                    answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer).strip()
                    
                    # Save to chat history
                    save_user_chat_history(current_user.id, session_id, mode, query, answer)
                    
                    # Extract structured data from answer
                    structured_data = extract_structured_data(answer, None, mode)
                    
                    log_ai_activity("Insights Query", "OpenAI", None, ai_duration)
                    chat_logger.info(f"Insights query processed for user {current_user.username}: {ai_duration:.2f}s")
                    
                    return jsonify({
                        "answer": answer,
                        "structured": structured_data
                    })
                    
                except Exception as e:
                    log_error(e, f"OpenAI Insights error for user {current_user.username}")
                    return jsonify({
                        "answer": "Sorry, the Insights mode encountered an error. Please try again."
                    })

            elif mode == "dealership":
                # Dealership Database Mode - LLM-powered SQL queries
                chat_logger.info(f"Processing Dealership query for user {current_user.username}")

                try:
                    from ai.dealership_engine import DealershipPipeline
                    from models.chat import get_user_chat_history

                    # Initialize dealership pipeline
                    dealership_pipeline = DealershipPipeline()

                    # Get chat history (already uses existing intent classifier for follow-ups)
                    history = get_user_chat_history(current_user.id, mode, session_id)
                    if len(history) == 0:
                        history = None

                    # Get answer from dealership pipeline
                    ai_start_time = time.time()
                    answer = dealership_pipeline.answer(query, chat_history=history)
                    ai_duration = time.time() - ai_start_time

                    # Save to chat history
                    save_user_chat_history(current_user.id, session_id, mode, query, answer)
                    structured_data = extract_structured_data(answer, None, mode)

                    log_ai_activity("Dealership Query", "Dealership Pipeline", None, ai_duration)
                    chat_logger.info(f"Dealership query processed for user {current_user.username}: {ai_duration:.2f}s")

                    return jsonify({
                        "answer": answer,
                        "structured": structured_data
                    })

                except Exception as e:
                    log_error(e, f"Dealership pipeline error for user {current_user.username}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({
                        "answer": "Sorry, dealership query failed. Please try rephrasing your question."
                    })

            elif mode == "facebook_beta":
                # Facebook Beta Mode - Process Facebook group data with advanced filtering
                chat_logger.info(f"Processing Facebook Beta query for user {current_user.username}")

                try:
                    from services.ai_service import AIService

                    # Get answer from AI service Facebook query processor
                    ai_start_time = time.time()
                    answer = AIService.process_chat_query(query, mode, user_company)
                    ai_duration = time.time() - ai_start_time

                    # Save to chat history
                    save_user_chat_history(current_user.id, session_id, mode, query, answer)
                    structured_data = extract_structured_data(answer, None, mode)

                    log_ai_activity("Facebook_Beta Query", "AI Service", None, ai_duration)
                    chat_logger.info(f"Facebook Beta query processed for user {current_user.username}: {ai_duration:.2f}s")

                    return jsonify({
                        "answer": answer,
                        "structured": structured_data
                    })

                except Exception as e:
                    log_error(e, f"Facebook Beta processing error for user {current_user.username}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({
                        "answer": "Sorry, Facebook Beta query failed. Please try rephrasing your question."
                    })

            # For RAG-based modes (PakWheels and WhatsApp), check pipeline status
            try:
                from ai.haval_pipeline import get_pipeline_status
                status = get_pipeline_status()
            except Exception as e:
                chat_logger.error(f"Error getting pipeline status: {e}")
                status = {"status": "error", "error": str(e)}
                
            if status.get("status") != "ready":
                # Try AI analysis as fallback for non-ready pipeline
                try:
                    from controllers.ai_analysis import ai_analyze_query
                    from models import get_db_connection
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Use AI analysis for intelligent responses
                    answer = ai_analyze_query(query, cur)
                    conn.close()
                    
                    # Save to chat history
                    save_user_chat_history(current_user.id, session_id, mode, query, answer)
                    
                    processing_time = time.time() - start_time
                    chat_logger.info(f"AI Analysis fallback used for user {current_user.username}: {processing_time:.2f}s")
                    
                    return jsonify({
                        "answer": answer,
                        "structured": {"references": [], "charts": [], "tables": [], "recommendations": []}
                    })
                    
                except Exception as fallback_error:
                    chat_logger.error(f"AI Analysis fallback failed: {fallback_error}")
                    # If pipeline is not ready and fallback fails, provide helpful message
                    import app
                    llm_client = app.get_llm_client()
                    if llm_client is None:
                        return jsonify({
                            "answer": (
                                "The AI system is not fully configured. Please ensure you have set up your API keys in the .env file:\n\n"
                                "1. XAI_API_KEY (for Grok) or GEMINI_API_KEY (for Gemini)\n"
                                "2. OPENAI_API_KEY (for Insights mode)\n\n"
                                "After adding the keys, restart the application."
                            )
                        })
                    else:
                        return jsonify({
                            "answer": (
                                f"The insight engine is still processing (current status: {status.get('status', 'unknown')}). "
                                "Please wait until it shows as ready, or try asking a general question in Insights mode."
                            )
                        })
            
            # Check if LLM client is available
            import app
            llm_client = app.get_llm_client()
            if llm_client is None:
                return jsonify({
                    "answer": (
                        "The AI system is not properly configured. Please check your API keys in the .env file and restart the application."
                    )
                })
            
            # Get user-specific chat history for the mode
            from models.chat import get_user_chat_history
            history = get_user_chat_history(current_user.id, mode, session_id)
            if len(history) == 0:
                history = None
            
            # Get company-specific RAG engine
            from config import get_company_config
            company_config = get_company_config(user_company)
            
            # Log which company is being queried
            chat_logger.info(f"Query for company: {company_config.full_name} (company_id: {user_company})")
            
            # Validate that the requested source is available for this company
            if mode == "whatsapp" and not company_config.has_whatsapp:
                return jsonify({
                    "answer": f"WhatsApp data is not available for {company_config.name}. "
                             f"Please select PakWheels or Insights mode."
                })
            elif mode == "pakwheels" and not company_config.has_pakwheels:
                return jsonify({
                    "answer": f"PakWheels data is not available for {company_config.name}. "
                             f"Please select a different data source."
                })
            
            # Use company-specific RAG engine
            try:
                from ai.haval_pipeline import get_rag_engine
                rag = get_rag_engine(company_id=user_company)
            except Exception as e:
                chat_logger.error(f"Error getting RAG engine: {e}")
                rag = None
                
            if rag is None:
                return jsonify({
                    "answer": f"The {company_config.name} insight engine is not available yet. "
                             f"Please try scraping {company_config.name} data first."
                })
            
            # Pass thinking_mode and source to RAG engine for filtering and formatting
            ai_start_time = time.time()
            answer = rag.answer(query, history=history, thinking_mode=thinking_mode, source=mode)
            ai_duration = time.time() - ai_start_time
            
            # Aggressive cleanup of any CHART_PLACEHOLDER patterns that LLM might output
            import re
            answer = re.sub(r'CHART_PLACEHOLDER_\d+', '', answer)
            answer = re.sub(r'__CHART_PLACEHOLDER_\d+__', '', answer)
            answer = re.sub(r'\bCHART_PLACEHOLDER_\d+\b', '', answer)
            answer = re.sub(r'CHART_PLACEHOLDER_\d+\s*', '', answer)
            answer = re.sub(r'\s*CHART_PLACEHOLDER_\d+', '', answer)
            answer = re.sub(r'\n\s*CHART_PLACEHOLDER_\d+\s*\n', '\n', answer)
            answer = re.sub(r'^CHART_PLACEHOLDER_\d+\s*\n', '', answer, flags=re.MULTILINE)
            # Remove any leftover empty lines or extra whitespace from cleanup
            answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer).strip()
            
            # Save to chat history
            save_user_chat_history(current_user.id, session_id, mode, query, answer)
            
            # Extract structured data from RAG answer
            structured_data = extract_structured_data(answer, None, mode)
            
            processing_time = time.time() - start_time
            log_ai_activity(f"{mode.title()} Query", "RAG Engine", None, ai_duration)
            chat_logger.info(f"{mode.title()} query processed for user {current_user.username}: {processing_time:.2f}s total")
            
            return jsonify({
                "answer": answer,
                "structured": structured_data
            })
            
        except Exception as e:
            log_error(e, f"Error processing chat query for user {current_user.username}")
            return jsonify({
                "answer": "Sorry, the insight engine ran into an error while answering. Please try again."
            })
    
    except Exception as e:
        log_error(e, f"Request processing error for user {current_user.username if current_user.is_authenticated else 'Anonymous'}")
        return jsonify({
            "answer": "Sorry, I could not generate a response."
        })


