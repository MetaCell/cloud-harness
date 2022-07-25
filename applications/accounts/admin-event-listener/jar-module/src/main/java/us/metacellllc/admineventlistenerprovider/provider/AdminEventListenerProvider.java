package us.metacellllc.admineventlistenerprovider.provider;

import org.keycloak.events.Event;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.admin.AdminEvent;
import org.keycloak.events.admin.ResourceType;
import org.keycloak.events.admin.OperationType;

import java.util.Map;

public class AdminEventListenerProvider implements EventListenerProvider {

    @Override
    public void onEvent(Event event) {
        // Do Nothing with normal events....
        // System.out.println("Event Occurred:" + toString(event));
    }

    @Override
    public void onEvent(AdminEvent adminEvent, boolean b) {
        onAdminEvent(adminEvent, b);
    }

    @Override
    public void close() {
    }

    private void onAdminEvent(AdminEvent adminEvent, boolean b) {
        System.out.println("Handle new Admin Event, resource path: " + adminEvent.getResourcePath());
        try {
            new AdminEventKafkaProducer().SendMessage(adminEvent.getResourceType().toString(), adminEvent.getOperationType().toString(), adminEvent.getResourcePath());
        } catch (Exception e) {
            System.out.println("Error Occurred:");
            System.out.println(e);
        }
    }

    private String toString(Event event) {
        StringBuilder sb = new StringBuilder();

        sb.append("type=");
        sb.append(event.getType());
        sb.append(", realmId=");
        sb.append(event.getRealmId());
        sb.append(", clientId=");
        sb.append(event.getClientId());
        sb.append(", userId=");
        sb.append(event.getUserId());
        sb.append(", ipAddress=");
        sb.append(event.getIpAddress());

        if (event.getError() != null) {
            sb.append(", error=");
            sb.append(event.getError());
        }

        if (event.getDetails() != null) {
            sb.append(", details: ");
            for (Map.Entry<String, String> e : event.getDetails().entrySet()) {
                sb.append(", ");
                sb.append(e.getKey());
                if (e.getValue() == null || e.getValue().indexOf(' ') == -1) {
                    sb.append("=");
                    sb.append(e.getValue());
                } else {
                    sb.append("='");
                    sb.append(e.getValue());
                    sb.append("'");
                }
            }
        }

        return sb.toString();
    }

    private String toString(AdminEvent adminEvent) {
        StringBuilder sb = new StringBuilder();

        sb.append("operationType=");
        sb.append(adminEvent.getOperationType());
        sb.append(", realmId=");
        sb.append(adminEvent.getAuthDetails().getRealmId());
        sb.append(", clientId=");
        sb.append(adminEvent.getAuthDetails().getClientId());
        sb.append(", userId=");
        sb.append(adminEvent.getAuthDetails().getUserId());
        sb.append(", ipAddress=");
        sb.append(adminEvent.getAuthDetails().getIpAddress());
        sb.append(", resourcePath=");
        sb.append(adminEvent.getResourcePath());

        if (adminEvent.getError() != null) {
            sb.append(", error=");
            sb.append(adminEvent.getError());
        }

        return sb.toString();
    }
}