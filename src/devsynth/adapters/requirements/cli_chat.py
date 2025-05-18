
"""
CLI chat adapter for requirements management.
"""
from typing import List, Optional
from uuid import UUID

from devsynth.domain.models.requirement import ChatMessage, ChatSession
from devsynth.ports.requirement_port import ChatPort, DialecticalReasonerPort


class CLIChatAdapter(ChatPort):
    """
    CLI implementation of the chat port.
    """
    
    def __init__(self, dialectical_reasoner: DialecticalReasonerPort):
        """
        Initialize the CLI chat adapter.
        
        Args:
            dialectical_reasoner: The dialectical reasoner service.
        """
        self.dialectical_reasoner = dialectical_reasoner
    
    def send_message(self, session_id: UUID, message: str, user_id: str) -> ChatMessage:
        """
        Send a message in a chat session.
        
        Args:
            session_id: The ID of the chat session.
            message: The message content.
            user_id: The ID of the user sending the message.
            
        Returns:
            The response message.
        """
        return self.dialectical_reasoner.process_message(session_id, message, user_id)
    
    def create_session(self, user_id: str, change_id: Optional[UUID] = None) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: The ID of the user.
            change_id: The ID of the change to discuss, if any.
            
        Returns:
            The created chat session.
        """
        return self.dialectical_reasoner.create_session(user_id, change_id)
    
    def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: The ID of the chat session.
            
        Returns:
            The chat session if found, None otherwise.
        """
        # This is delegated to the dialectical reasoner, which uses the chat repository
        # We could implement this directly using the chat repository, but for simplicity,
        # we'll reuse the dialectical reasoner's implementation
        session = self.dialectical_reasoner.create_session("system")  # Create a temporary session
        # This is a hack to get access to the chat repository
        return self.dialectical_reasoner.chat_repository.get_session(session_id)
    
    def get_sessions_for_user(self, user_id: str) -> List[ChatSession]:
        """
        Get chat sessions for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            A list of chat sessions for the user.
        """
        # Similar to get_session, we'll use the dialectical reasoner's chat repository
        session = self.dialectical_reasoner.create_session("system")  # Create a temporary session
        return self.dialectical_reasoner.chat_repository.get_sessions_for_user(user_id)
    
    def get_messages_for_session(self, session_id: UUID) -> List[ChatMessage]:
        """
        Get messages for a chat session.
        
        Args:
            session_id: The ID of the chat session.
            
        Returns:
            A list of messages for the chat session.
        """
        # Similar to get_session, we'll use the dialectical reasoner's chat repository
        session = self.dialectical_reasoner.create_session("system")  # Create a temporary session
        return self.dialectical_reasoner.chat_repository.get_messages_for_session(session_id)
    
    def display_message(self, message: ChatMessage) -> None:
        """
        Display a chat message in the CLI.
        
        Args:
            message: The message to display.
        """
        sender = message.sender
        content = message.content
        
        if sender == "system":
            print(f"\n[System] {content}\n")
        else:
            print(f"\n[{sender}] {content}\n")
    
    def run_interactive_session(self, session_id: UUID, user_id: str) -> None:
        """
        Run an interactive chat session in the CLI.
        
        Args:
            session_id: The ID of the chat session.
            user_id: The ID of the user.
        """
        session = self.get_session(session_id)
        if not session:
            print(f"Error: Session with ID {session_id} not found.")
            return
        
        # Display existing messages
        messages = self.get_messages_for_session(session_id)
        for message in messages:
            self.display_message(message)
        
        # Interactive loop
        print("\nEnter your messages below. Type 'exit' to end the session.\n")
        while True:
            user_input = input(f"[{user_id}] ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nEnding chat session. Goodbye!\n")
                break
            
            # Send the message and get the response
            response = self.send_message(session_id, user_input, user_id)
            
            # Display the response
            self.display_message(response)
