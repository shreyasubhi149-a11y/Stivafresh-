self.addEventListener("install", function(event) {
    console.log("StivaFresh service worker installed");
    self.skipWaiting();
});

self.addEventListener("activate", function(event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("push", function(event) {
    let data = {
        title: "StivaFresh 🌱",
        body: "You have a grocery reminder!"
    };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (error) {
            data.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: "/static/stivafresh_logo.png",
            badge: "/static/stivafresh_logo.png"
        })
    );
});

self.addEventListener("notificationclick", function(event) {
    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true })
            .then(function(clientList) {
                for (const client of clientList) {
                    if ("focus" in client) {
                        return client.focus();
                    }
                }

                if (clients.openWindow) {
                    return clients.openWindow("/");
                }
            })
    );
});

self.addEventListener("fetch", function(event) {
    // Allows the app to handle requests
});
// The current template posts expiry reminders while the page is running.
self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'EXPIRY_REMINDER') {
        event.waitUntil(self.registration.showNotification('StivaFresh', {
            body: event.data.message || 'Review your tracked groceries.',
            icon: '/static/stivafresh_logo.png',
            tag: 'stivafresh-expiry'
        }));
    }
});
