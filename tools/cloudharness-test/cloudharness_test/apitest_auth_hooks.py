import os
import logging
import schemathesis as st
from cloudharness.auth import get_token


@st.auth()
class TokenAuth:
    """
    Schemathesis authentication hook that retrieves a bearer token
    using Keycloak credentials and sets both Authorization header and Cookie.
    
    Requires USERNAME and PASSWORD environment variables to be set.
    """
    
    def get(self, context):
        """
        Retrieve the authentication token using username and password from environment.
        
        Args:
            context: Schemathesis hook context
            
        Returns:
            str: The bearer token
            
        Raises:
            ValueError: If USERNAME or PASSWORD environment variables are not set
            Exception: If token retrieval fails
        """
        username = os.environ.get("USERNAME")
        password = os.environ.get("PASSWORD")
        
        if not username or not password:
            logging.warning("USERNAME and/or PASSWORD environment variables not set. Skipping authentication.")
            return None
        
        try:
            token = get_token(username, password)
            if not token:
                logging.warning("Token retrieval returned empty token for user %s", username)
                return None
            logging.info("Successfully retrieved authentication token for user %s", username)
            return token
        except Exception as e:
            logging.error("Failed to retrieve bearer token for user %s: %s", username, e)
            raise
    
    def set(self, case, data, context):
        """
        Set the authentication token in the request headers and cookies.
        
        Args:
            case: Schemathesis test case
            data: The authentication token
            context: Schemathesis hook context
        """
        if not data:
            return
        
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {data}"
        case.headers["Cookie"] = f"kc-access={data}"

