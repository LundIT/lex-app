from adrf.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any
import asyncio
import json

from rest_framework_api_key.permissions import HasAPIKey


class ApprovalType(Enum):
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    TEST_EXECUTION = "test_execution"


@dataclass
class ApprovalRequest:
    """Represents a pending approval request"""
    request_id: str
    approval_type: ApprovalType
    content: Dict[str, Any]
    status: Optional[bool] = None
    feedback: Optional[str] = None


class ApprovalRegistry:
    """Singleton registry for managing approval requests and their events"""
    _instance = None
    _requests: Dict[str, ApprovalRequest] = {}
    _events: Dict[str, asyncio.Event] = {}
    APPROVAL_ON = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def create_request(self, approval_type: ApprovalType, content: Dict[str, Any]) -> str:
        """Create a new approval request and return its ID"""
        request_id = f"{approval_type.value}_{len(self._requests)}"
        request = ApprovalRequest(request_id, approval_type, content)
        event = asyncio.Event()

        self._requests[request_id] = request
        self._events[request_id] = event
        return request_id

    async def wait_for_approval(self, request_id: str) -> ApprovalRequest:
        """Wait for approval response"""
        if request_id not in self._events:
            raise ValueError(f"Invalid request ID: {request_id}")
        await self._events[request_id].wait()
        return self._requests[request_id]

    def handle_response(self, request_id: str, approved: bool, content=None, feedback: Optional[str] = None):
        """Handle approval response"""
        if request_id not in self._requests:
            raise ValueError(f"Invalid request ID: {request_id}")

        request = self._requests[request_id]
        request.status = approved
        request.feedback = feedback
        request.content = content or request.content
        self._events[request_id].set()


class ApprovalView(APIView):
    """Handles approval requests and responses"""
    permission_classes = [IsAuthenticated | HasAPIKey]
    async def get(self, request):
        """Get all pending approval requests"""
        registry = ApprovalRegistry()
        pending_requests = [
            {
                'request_id': req.request_id,
                'type': req.approval_type.value,
                'content': req.content,
                'status': req.status
            }
            for req in registry._requests.values()
            if req.status is None
        ]
        return Response({'pending_requests': pending_requests})

    async def post(self, request):
        """Handle approval/rejection response"""
        try:
            request_id = request.data.get('request_id')
            approved = request.data.get('approved')
            feedback = request.data.get('feedback')
            content = request.data.get('content')

            if not request_id or approved is None:
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            registry = ApprovalRegistry()
            registry.handle_response(request_id, approved, content, feedback)
            return Response({'status': 'success'})

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )