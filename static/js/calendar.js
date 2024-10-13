function renderCalendar(activityData) {
    const calendarElement = document.getElementById('calendar');
    const monthLabelsElement = document.getElementById('month-labels');
    if (!calendarElement || !monthLabelsElement) {
        console.error('Calendar or month labels element not found');
        return;
    }
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());

    // Clear existing calendar
    calendarElement.innerHTML = '';
    monthLabelsElement.innerHTML = '';

    // Generate month labels
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    let currentMonth = oneYearAgo.getMonth();
    for (let i = 0; i < 12; i++) {
        const monthLabel = document.createElement('span');
        monthLabel.textContent = months[(currentMonth + i) % 12];
        monthLabelsElement.appendChild(monthLabel);
    }

    // Generate calendar days
    let currentDate = new Date(oneYearAgo);
    while (currentDate <= today) {
        const dayElement = document.createElement('div');
        dayElement.classList.add('calendar-day');

        const dateString = currentDate.toISOString().split('T')[0];
        const activityLevel = activityData[dateString] || 0;

        // Set background color based on activity level
        const bgColor = getColorForActivityLevel(activityLevel);
        dayElement.style.backgroundColor = bgColor;

        // Add event listeners for mouseover and click
        dayElement.addEventListener('mouseover', () => showActivityDetails(dateString, dayElement));
        dayElement.addEventListener('click', () => showActivityDetails(dateString, dayElement, true));

        calendarElement.appendChild(dayElement);
        currentDate.setDate(currentDate.getDate() + 1);
    }
}

function getColorForActivityLevel(level) {
    if (level === 0) return '#ebedf0';  // Very light grey for no activity
    if (level <= 0.25) return '#9be9a8';  // Light green
    if (level <= 0.5) return '#40c463';  // Medium green
    if (level <= 0.75) return '#30a14e';  // Dark green
    return '#216e39';  // Very dark green for high activity
}

function showActivityDetails(date, element, isPermanent = false) {
    // Remove existing tooltips
    const existingTooltip = document.querySelector('.activity-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }

    // Fetch activity details
    fetch(`/activity_details/${date}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const tooltip = document.createElement('div');
            tooltip.classList.add('activity-tooltip');
            
            if (data.error) {
                tooltip.innerHTML = `<strong>Error:</strong> ${data.error}`;
            } else {
                tooltip.innerHTML = `
                    <strong>Date:</strong> ${date}<br>
                    <strong>Activity Level:</strong> ${(data.activity_level * 100).toFixed(2)}%<br>
                    <strong>Activities:</strong> ${data.activities.length > 0 ? data.activities.join(', ') : 'No activities recorded'}
                `;
            }

            // Position the tooltip
            const rect = element.getBoundingClientRect();
            tooltip.style.position = 'absolute';
            tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
            tooltip.style.left = `${rect.left + window.scrollX - 100}px`;
            tooltip.style.zIndex = '1000';
            tooltip.style.backgroundColor = 'var(--bs-dark)';
            tooltip.style.color = 'var(--bs-light)';
            tooltip.style.padding = '10px';
            tooltip.style.borderRadius = '5px';
            tooltip.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
            tooltip.style.width = '200px';
            tooltip.style.fontSize = '12px';

            document.body.appendChild(tooltip);

            if (!isPermanent) {
                element.addEventListener('mouseout', () => tooltip.remove());
            } else {
                tooltip.style.cursor = 'pointer';
                tooltip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    tooltip.remove();
                });
                document.addEventListener('click', () => tooltip.remove(), { once: true });
            }
        })
        .catch(error => {
            console.error('Error fetching activity details:', error);
        });
}

// Initialize the calendar when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const activityDataElement = document.getElementById('activity-data');
    if (activityDataElement) {
        const activityData = JSON.parse(activityDataElement.textContent);
        renderCalendar(activityData);
    } else {
        console.error('Activity data element not found');
    }
});
