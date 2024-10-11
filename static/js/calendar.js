document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('workoutCalendar').getContext('2d');
    let workoutData = {};
    let chart;

    function createCalendar(data) {
        const today = new Date();
        const startDate = new Date(today.getFullYear(), today.getMonth() - 11, 1);
        const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        const datasets = [];
        const labels = [];

        let currentDate = new Date(startDate);
        while (currentDate <= endDate) {
            const dateString = currentDate.toISOString().split('T')[0];
            labels.push(dateString);
            const duration = data[dateString] || 0;
            datasets.push({
                x: dateString,
                y: currentDate.getDay(),
                d: duration
            });
            currentDate.setDate(currentDate.getDate() + 1);
        }

        chart = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Workout Duration',
                    data: datasets,
                    backgroundColor(context) {
                        const value = context.dataset.data[context.dataIndex].d;
                        const alpha = value > 0 ? Math.min(value / 60, 1) : 0;
                        return `rgba(40, 167, 69, ${alpha})`;
                    },
                    borderColor: '#1a1a1a',
                    borderWidth: 1,
                    width: ({ chart }) => (chart.chartArea || {}).width / 53 - 1,
                    height: ({ chart }) => (chart.chartArea || {}).height / 7 - 1,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            round: 'month',
                            displayFormats: {
                                month: 'MMM'
                            }
                        },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12
                        }
                    },
                    y: {
                        type: 'category',
                        labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                        offset: true,
                        position: 'right',
                        reverse: true,
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return new Date(context[0].raw.x).toDateString();
                            },
                            label: function(context) {
                                const duration = context.raw.d;
                                return duration > 0 ? `Duration: ${duration} minutes` : 'No workout';
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function fetchWorkouts() {
        fetch('/api/workouts')
            .then(response => response.json())
            .then(data => {
                workoutData = data.reduce((acc, workout) => {
                    acc[workout.date] = (acc[workout.date] || 0) + workout.duration;
                    return acc;
                }, {});
                createCalendar(workoutData);
            });
    }

    function fetchStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalWorkouts').textContent = data.total_workouts;
                document.getElementById('currentStreak').textContent = data.current_streak;
                document.getElementById('mostActiveDay').textContent = data.most_active_day ? new Date(data.most_active_day).toDateString() : 'N/A';
            });
    }

    document.getElementById('addWorkoutForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const date = document.getElementById('date').value;
        const duration = parseInt(document.getElementById('duration').value);
        const exerciseType = document.getElementById('exerciseType').value;

        fetch('/api/add_workout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date, duration, exercise_type: exerciseType }),
        })
        .then(response => response.json())
        .then(data => {
            workoutData[data.date] = (workoutData[data.date] || 0) + data.duration;
            chart.update();
            fetchStats();
            e.target.reset();
        });
    });

    fetchWorkouts();
    fetchStats();
});
