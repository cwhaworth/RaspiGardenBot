document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById('tempChart').getContext('2d');
    if (!ctx || !window.sysData) return;

    const canvas = document.getElementById('tempChart');
    const styles = getComputedStyle(canvas);
    const data = {
        labels: window.sysData.timestamp,
        datasets: [{
            // label: 'System Temperature (°F)',
            data: window.sysData.temp,
            // borderColor: 'rgb(34, 139, 34)',
            borderColor: styles.getPropertyValue('--line-color'),
            // backgroundColor: 'rgba(34, 139, 34, 0.2)',
            backgroundColor: styles.getPropertyValue('--fill-color'),
            fill: false,
            tension: 0.4
        }]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                    position: 'top'
                },
                title: {
                    display: false,
                    text: 'System Temperature Over Time'
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Timestamp',
                        color: '#E1E2E0'
                    }
                },
                y: {
                    ticks: {
                        color: '#E1E2E0'
                    },
                    title: {
                        display: true,
                        text: 'Temperature',
                        color: '#E1E2E0'
                    }
                }
            }
        }
    };

    const tempChart = new Chart(ctx, config);
});