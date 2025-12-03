import os
import traceback
from typing import Any
from uuid import uuid4

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    SendMessageResponse,
    GetTaskResponse,
    SendMessageSuccessResponse,
    Task,
    TaskState,
    SendMessageRequest,
    MessageSendParams,
    GetTaskRequest,
    TaskQueryParams,
)
import httpx

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:10001")


def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
    """Helper function to create the payload for sending a message."""
    payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }

    if task_id:
        payload["message"]["taskId"] = task_id

    if context_id:
        payload["message"]["contextId"] = context_id
    return payload


def print_json_response(response: Any, description: str) -> None:
    """Helper function to print the JSON representation of a response."""
    print(f"--- {description} ---")
    if hasattr(response, "root"):
        print(f"{response.root.model_dump_json(exclude_none=True)}\n")
    else:
        print(f"{response.model_dump(mode='json', exclude_none=True)}\n")


async def run_single_turn_test(client: A2AClient) -> None:
    """Runs a single-turn non-streaming test."""

    send_message_payload = create_send_message_payload(text="Tell me about Pikachu")
    request = SendMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    )

    print("--- ✉️  Single Turn Request ---")
    # Send Message
    response: SendMessageResponse = await client.send_message(request)
    print_json_response(response, "📥 Single Turn Request Response")
    if not isinstance(response.root, SendMessageSuccessResponse):
        print("received non-success response. Aborting get task ")
        return

    if not isinstance(response.root.result, Task):
        print("received non-task response. Aborting get task ")
        return

    task_id: str = response.root.result.id
    print("--- ❔ Query Task ---")
    # query the task
    get_request = GetTaskRequest(id=str(uuid4()), params=TaskQueryParams(id=task_id))
    get_response: GetTaskResponse = await client.get_task(get_request)
    print_json_response(get_response, "📥 Query Task Response")


async def run_multi_turn_test(client: A2AClient) -> None:
    """Runs a multi-turn non-streaming test."""
    print("--- 📝 Multi-Turn Request ---")
    # --- First Turn ---

    first_turn_payload = create_send_message_payload(text="What are the stats for Charizard?")
    request1 = SendMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**first_turn_payload)
    )
    first_turn_response: SendMessageResponse = await client.send_message(request1)
    print_json_response(first_turn_response, "📥 Multi-Turn: First Turn Response")

    context_id: str | None = None
    if isinstance(first_turn_response.root, SendMessageSuccessResponse) and isinstance(
        first_turn_response.root.result, Task
    ):
        task: Task = first_turn_response.root.result
        context_id = task.context_id  # Capture context ID

        # --- Second Turn (if input required) ---
        if task.status.state == TaskState.input_required and context_id:
            print("--- 📝 Multi-Turn: Second Turn (Input Required) ---")
            second_turn_payload = create_send_message_payload(
                "Now tell me about its evolution line", task.id, context_id
            )
            request2 = SendMessageRequest(
                id=str(uuid4()), params=MessageSendParams(**second_turn_payload)
            )
            second_turn_response = await client.send_message(request2)
            print_json_response(
                second_turn_response, "Multi-Turn: Second Turn Response"
            )
        elif not context_id:
            print(
                "--- ⚠️ Warning: Could not get context ID from first turn response. ---"
            )
        else:
            print(
                "--- 🚀 First turn completed, no further input required for this test case. ---"
            )


async def run_pokemon_search_test(client: A2AClient) -> None:
    """Runs a Pokemon search test."""
    print("--- 🔍 Pokemon Search Test ---")

    search_payload = create_send_message_payload(text="Show me a list of Pokemon starting from number 50")
    request = SendMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**search_payload)
    )
    
    response: SendMessageResponse = await client.send_message(request)
    print_json_response(response, "📥 Pokemon Search Response")

    if isinstance(response.root, SendMessageSuccessResponse) and isinstance(response.root.result, Task):
        task_id: str = response.root.result.id
        get_request = GetTaskRequest(id=str(uuid4()), params=TaskQueryParams(id=task_id))
        get_response: GetTaskResponse = await client.get_task(get_request)
        print_json_response(get_response, "📥 Pokemon Search Task Response")


async def run_pokemon_species_test(client: A2AClient) -> None:
    """Runs a Pokemon species information test."""
    print("--- 🧬 Pokemon Species Test ---")

    species_payload = create_send_message_payload(text="What is the description of Bulbasaur?")
    request = SendMessageRequest(
        id=str(uuid4()), params=MessageSendParams(**species_payload)
    )
    
    response: SendMessageResponse = await client.send_message(request)
    print_json_response(response, "📥 Pokemon Species Response")

    if isinstance(response.root, SendMessageSuccessResponse) and isinstance(response.root.result, Task):
        task_id: str = response.root.result.id
        get_request = GetTaskRequest(id=str(uuid4()), params=TaskQueryParams(id=task_id))
        get_response: GetTaskResponse = await client.get_task(get_request)
        print_json_response(get_response, "📥 Pokemon Species Task Response")


async def main() -> None:
    """Main function to run the tests."""
    print(f"--- 🔄 Connecting to Pokemon agent at {AGENT_URL}... ---")
    try:
        # Increase timeout to 60 seconds for all operations
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            # Create a resolver to fetch the agent card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=AGENT_URL,
            )
            agent_card = await resolver.get_agent_card()
            # Create a client to interact with the agent
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card,
            )
            print("--- ✅ Connection successful. ---")

            # Test different Pokemon agent capabilities
            await run_single_turn_test(client)
            await run_pokemon_search_test(client)
            await run_pokemon_species_test(client)
            # await run_multi_turn_test(client)

    except Exception as e:
        traceback.print_exc()
        print(f"--- ❌ An error occurred: {e} ---")
        print("Ensure the Pokemon agent server is running.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())