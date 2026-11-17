import { useState, useEffect } from 'react';

type User = {
  username: string;
  first_name: string;
  last_name: string;
  roles: string[];
};

// set by Django on the page that serves the frontend
const getCsrfToken = () =>
  document.cookie.split("; ").find(c => c.startsWith("csrftoken="))?.split("=")[1] ?? "";

const CurrentUser = () => {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    fetch("/api/me", { headers: { 'Accept': 'application/json' } }).then(r => {
      if (r.status === 401) {
        // session expired: log in again and come back here
        window.location.href = `/oidc/login/?next=${encodeURIComponent(window.location.pathname)}`;
        return;
      }
      if (r.ok) {
        return r.json().then(setUser);
      }
    });
  }, []);

  if (!user) {
    return null;
  }
  return (
    <form method="post" action="/oidc/logout/">
      <input type="hidden" name="csrfmiddlewaretoken" value={getCsrfToken()} />
      Logged in as {user.first_name} {user.last_name} ({user.username}) - roles: {user.roles.join(", ") || "none"} -{" "}
      <button type="submit">Log out</button>
    </form>
  );
}

export default CurrentUser;
