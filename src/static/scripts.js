// Example for using Chart.js to render charts
document.addEventListener('DOMContentLoaded', () => {
    const ctx1 = document.getElementById('trendChart').getContext('2d');
    const ctx2 = document.getElementById('pollutionChart').getContext('2d');
  
    new Chart(ctx1, {
      type: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
          label: 'Trend',
          data: [200, 300, 400, 500, 450, 300, 200],
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2
        }]
      },
      options: { responsive: true }
    });
  
    new Chart(ctx2, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
          label: 'Pollution',
          data: [500, 600, 700, 650, 600, 580, 590, 600, 610, 620, 630, 640],
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2
        }]
      },
      options: { responsive: true }
    });
  });

    // Show/hide dropdown menu
document.getElementById('settingsDropdown').addEventListener('click', function() {
    var dropdownMenu = document.querySelector('.dropdown-menu');
    dropdownMenu.style.display = (dropdownMenu.style.display === 'block') ? 'none' : 'block';
  });
