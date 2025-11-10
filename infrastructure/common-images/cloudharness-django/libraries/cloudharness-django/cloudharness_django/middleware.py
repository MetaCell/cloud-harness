
import jwt

from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.db import transaction
from keycloak.exceptions import KeycloakGetError

from cloudharness.auth.exceptions import InvalidToken
from cloudharness_django.services import get_user_service
from .models import Member
from cloudharness import log
from cloudharness.auth.keycloak import get_current_user_id, User as KcUser
from psycopg2.errors import UniqueViolation


def _get_user(kc_user_id: str) -> User:
    """
    Get or create a Django user for the given Keycloak user ID.
    
    CRITICAL SAFETY GUARANTEE: This function will NEVER return a User without a valid Member.
    If we cannot ensure a Member exists, we return None (which triggers anonymous user behavior).
    
    Returns:
        User: A Django User with a guaranteed Member relationship, or None for anonymous
    """
    user = None
    if kc_user_id is None:
        return None
    
    try:
        # Try to get existing user by member relationship
        try:
            user = User.objects.get(member__kc_id=kc_user_id)
            
            # SAFETY CHECK: Verify member relationship is intact
            try:
                _ = user.member  # Access to verify it exists
            except Member.DoesNotExist:
                # Member was deleted between the query and now - return None for safety
                log.error("User %s found but Member missing. Returning anonymous.", user.id)
                return None
                
        except User.DoesNotExist:
            # User doesn't exist - create it via sync_kc_user
            user_svc = get_user_service()
            kc_user = user_svc.auth_client.get_current_user()
            try:
                # sync_kc_user is atomic and guarantees Member creation
                user = user_svc.sync_kc_user(kc_user)
                user_svc.sync_kc_user_groups(kc_user)
                
                # SAFETY CHECK: Final verification that Member exists
                try:
                    _ = user.member
                except Member.DoesNotExist:
                    # This should NEVER happen due to sync_kc_user safety, but be defensive
                    log.error("sync_kc_user returned user %s without Member! Returning anonymous.", user.id)
                    return None
                    
            except UniqueViolation as e:
                # Race condition while creating the Member object
                log.warning("UniqueViolation error for kc_id %s. Probably a race condition. %s", kc_user_id, str(e))
                # Try to get the user again
                try:
                    user = User.objects.get(member__kc_id=kc_user_id)
                    # Verify member exists
                    _ = user.member
                except (User.DoesNotExist, Member.DoesNotExist):
                    log.error("Failed to retrieve user after UniqueViolation. Returning anonymous.")
                    return None
                    
        except User.MultipleObjectsReturned:
            # Race condition, multiple users created for the same kc_id
            log.warning("Multiple users found for kc_id %s, cleaning up...", kc_user_id)
            user = User.objects.filter(member__kc_id=kc_user_id).order_by('id').first()
            User.objects.filter(member__kc_id=kc_user_id).exclude(id=user.id).delete()
            
            # SAFETY CHECK: Verify the kept user has a Member
            try:
                _ = user.member
            except:
                log.error("Cleaned up user %s has no Member. Returning anonymous.", user.id)
                return None
            
            return user

        except Exception as e:
            log.exception("User sync error, %s", kc_user.email)
            return None
            
        return user
        
    except KeycloakGetError:
        # KC user not found
        return None
    except InvalidToken:
        return None
    except Exception as e:
        log.exception("User %s mapping error, %s", kc_user_id, e)
        return None


class BearerTokenMiddleware:
    def __init__(self, get_response=None):
        # One-time configuration and initialization.
        self.get_response = get_response

    @transaction.atomic
    def __call__(self, request):
        user = getattr(request, "user", None)

        kc_user = get_current_user_id()
        if kc_user:
            if not user or user.is_anonymous or getattr(user, "member", None) is None or user.member.kc_id != kc_user.id:
                user = _get_user(kc_user)
                if user:
                    # CRITICAL SAFETY CHECK: Never assign user without Member
                    # This is the final defense to ensure request.user always has a Member
                    try:
                        _ = user.member  # Verify member exists
                        # Safe to assign - user has a valid Member
                        request.user = user
                        request._cached_user = user
                    except:
                        # This should NEVER happen due to _get_user safety checks,
                        # but if it does, DO NOT assign the user - keep anonymous
                        log.error("CRITICAL: _get_user returned user %s without Member! Keeping anonymous.", user.id)
                        logout(request)
                        # Don't assign user - request will remain anonymous
        # elif not request.path.startswith('/admin/'):
        #     logout(request)

        return self.get_response(request)


class BearerTokenAuthentication:
    # for django rest framework usage
    def authenticate(self, request):
        kc_user = get_current_user_id()
        if not kc_user:
            return None
        user: User = getattr(request._request, 'user', None)
        if user and user.is_authenticated:
            # SAFETY CHECK: Verify authenticated user has Member
            try:
                _ = user.member
                return (user, None)
            except Member.DoesNotExist:
                log.error("Authenticated user %s has no Member! Falling back to _get_user.", user.id)
                # Fall through to _get_user which will handle this safely
        
        # Get or create user with guaranteed Member
        user = _get_user(kc_user)
        if user:
            # FINAL SAFETY CHECK: Ensure Member exists before returning
            try:
                _ = user.member
                return (user, None)
            except Member.DoesNotExist:
                log.error("CRITICAL: _get_user returned user %s without Member! Returning None.", user.id)
                return None
        
        return None
