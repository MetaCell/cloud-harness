#! /bin/bash

/opt/keycloak/bin/kc.sh $@ &


# Run startup scripts to create admin_api user
for script in /opt/keycloak/startup-scripts/*.sh;
    do
        echo "Running startup script: $script"
        if bash "$script"; then
            echo "Successfully executed $script"
        else
            echo "Warning: $script failed with exit code $?"
    fi
done

wait