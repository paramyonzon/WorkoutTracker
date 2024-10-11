document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('workoutProgressChart').getContext('2d');
    let chart;

    function fetchWorkoutProgress() {
        fetch('/api/workout_progress')
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.date);
                const totalDurations = data.map(item => item.total_duration);

                if (chart) {
                    chart.destroy();
                }

                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Total Workout Duration (minutes)',
                            data: totalDurations,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'day'
                                },
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Total Duration (minutes)'
                                }
                            }
                        }
                    }
                });
            });
    }

    fetchWorkoutProgress();

    // Update the chart when a new workout is added
    document.getElementById('addWorkoutForm').addEventListener('submit', function(e) {
        e.preventDefault();
        // ... (existing code for adding a workout)
        .then(() => {
            fetchWorkoutProgress();
        });
    });
});
