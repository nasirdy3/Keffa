let notificationPermission = false;

async function requestNotificationPermission() {
    if ('Notification' in window && 'serviceWorker' in navigator) {
        try {
            const permission = await Notification.requestPermission();
            notificationPermission = permission === 'granted';
            
            if (notificationPermission) {
                console.log('✓ Notification permission granted');
                
                const registration = await navigator.serviceWorker.ready;
                console.log('✓ Service Worker ready');
            } else {
                console.log('✗ Notification permission denied');
            }
            
            return notificationPermission;
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }
    return false;
}

function showLocalNotification(title, options = {}) {
    if (!notificationPermission) {
        console.log('Notifications not permitted');
        return;
    }
    
    const defaultOptions = {
        badge: '/static/images/icon-192.png',
        icon: '/static/images/icon-192.png',
        vibrate: [200, 100, 200],
        requireInteraction: false,
        ...options
    };
    
    if ('serviceWorker' in navigator && 'Notification' in window) {
        navigator.serviceWorker.ready.then(registration => {
            registration.showNotification(title, defaultOptions);
        });
    } else if (notificationPermission) {
        new Notification(title, defaultOptions);
    }
}

function notifyMatchReady(matchInfo) {
    showLocalNotification('Match Ready! ⚽', {
        body: `Your match against ${matchInfo.opponent} is starting soon. Click "Ready" within 5 minutes!`,
        tag: `match-ready-${matchInfo.matchId}`,
        requireInteraction: true,
        actions: [
            { action: 'view', title: 'View Match' }
        ],
        data: {
            url: `/matches/${matchInfo.matchId}/ready/`
        }
    });
}

function notifyTournamentLocked(tournamentInfo) {
    showLocalNotification('Tournament Locked! 🏆', {
        body: `${tournamentInfo.name} is now full and fixtures have been generated!`,
        tag: `tournament-locked-${tournamentInfo.tournamentId}`,
        data: {
            url: `/tournaments/${tournamentInfo.tournamentId}/`
        }
    });
}

function notifyPaymentConfirmed(tournamentInfo) {
    showLocalNotification('Payment Confirmed! ✅', {
        body: `Your registration for ${tournamentInfo.name} has been confirmed. Good luck!`,
        tag: `payment-confirmed-${tournamentInfo.tournamentId}`,
        data: {
            url: `/tournaments/${tournamentInfo.tournamentId}/`
        }
    });
}

function notifyAchievementEarned(achievementInfo) {
    showLocalNotification('Achievement Unlocked! 🏅', {
        body: `Congratulations! You earned: ${achievementInfo.name}`,
        tag: `achievement-${achievementInfo.badgeId}`,
        requireInteraction: true,
        data: {
            url: '/players/dashboard/'
        }
    });
}

function notifyHighlightDeadline(matchInfo) {
    showLocalNotification('Highlight Upload Reminder ⏰', {
        body: `Don't forget to upload your highlight for ${matchInfo.opponent}. Deadline: ${matchInfo.deadline}`,
        tag: `highlight-deadline-${matchInfo.matchId}`,
        requireInteraction: true,
        data: {
            url: `/highlights/upload/${matchInfo.matchId}/`
        }
    });
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', event => {
        if (event.data && event.data.type === 'notification-click') {
            if (event.data.url) {
                window.location.href = event.data.url;
            }
        }
    });
}

window.addEventListener('load', () => {
    if ('Notification' in window && Notification.permission === 'default') {
        setTimeout(() => {
            const banner = document.createElement('div');
            banner.className = 'alert alert-info';
            banner.style.position = 'fixed';
            banner.style.top = '80px';
            banner.style.left = '50%';
            banner.style.transform = 'translateX(-50%)';
            banner.style.zIndex = '9999';
            banner.style.maxWidth = '500px';
            banner.style.margin = '0 1rem';
            banner.innerHTML = `
                <strong>🔔 Stay Updated!</strong> Enable notifications to get match alerts, tournament updates, and achievement notifications.
                <button onclick="requestNotificationPermission().then(() => this.parentElement.remove())" class="btn btn-sm btn-primary" style="margin-left: 1rem;">Enable</button>
                <button onclick="this.parentElement.remove()" class="btn btn-sm" style="margin-left: 0.5rem;">Later</button>
            `;
            document.body.appendChild(banner);
            
            setTimeout(() => {
                if (banner.parentElement) {
                    banner.style.opacity = '0';
                    banner.style.transition = 'opacity 0.5s';
                    setTimeout(() => banner.remove(), 500);
                }
            }, 15000);
        }, 3000);
    }
});

window.notificationUtils = {
    request: requestNotificationPermission,
    matchReady: notifyMatchReady,
    tournamentLocked: notifyTournamentLocked,
    paymentConfirmed: notifyPaymentConfirmed,
    achievementEarned: notifyAchievementEarned,
    highlightDeadline: notifyHighlightDeadline
};
