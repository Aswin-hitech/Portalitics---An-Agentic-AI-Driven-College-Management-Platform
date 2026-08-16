// PORTALITICS Academic Chart Engine (Lucid Design System)

document.addEventListener('DOMContentLoaded', () => {
  initStudentCharts();
  initFacultyCharts();
  initAdminCharts();
});

function setChartState(canvas, state, message) {
  if (!canvas) return;
  canvas.dataset.state = state;
  const wrapper = canvas.closest('.chart-box');
  if (!wrapper) return;
  let status = wrapper.querySelector('.chart-state');
  if (!status) {
    status = document.createElement('div');
    status.className = 'chart-state';
    wrapper.appendChild(status);
  }
  status.textContent = message || '';
  status.classList.toggle('is-loading', state === 'loading');
  status.classList.toggle('is-error', state === 'error');
  status.classList.toggle('is-empty', state === 'empty');
}

// --- Student Dashboard Charts ---
async function initStudentCharts() {
  const attCanvas = document.getElementById('studentAttendanceChart');
  const cgpaCanvas = document.getElementById('studentCgpaChart');
  const assignCanvas = document.getElementById('studentAssignmentPieChart');
  const scatterCanvas = document.getElementById('studentExamScatterChart');

  if (!attCanvas && !cgpaCanvas && !assignCanvas && !scatterCanvas) return;

  try {
    [attCanvas, cgpaCanvas, assignCanvas, scatterCanvas].forEach((canvas) => setChartState(canvas, 'loading', 'Loading chart data...'));
    const res = await fetch('/student/api/charts');
    if (!res.ok) throw new Error('Unable to load student charts');
    const data = await res.json();

    if (attCanvas && data.attendance_trend) {
      const ctx = attCanvas.getContext('2d');
      const grad = ctx.createLinearGradient(0, 0, 0, 260);
      grad.addColorStop(0, 'rgba(107, 30, 45, 0.12)');
      grad.addColorStop(1, 'rgba(107, 30, 45, 0.0)');

      new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.attendance_trend.labels,
          datasets: [{
            label: 'Attendance %',
            data: data.attendance_trend.data,
            borderColor: '#6B1E2D',
            backgroundColor: grad,
            fill: true,
            tension: 0.35,
            borderWidth: 2.2,
            pointBackgroundColor: '#6B1E2D',
            pointBorderColor: '#FFFFFF',
            pointRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: '#555555' } },
            y: { min: 40, max: 100, grid: { color: '#E5E2DF' }, ticks: { color: '#555555' } }
          }
        }
      });
    }

    if (cgpaCanvas && data.cgpa_progression) {
      new Chart(cgpaCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: data.cgpa_progression.labels,
          datasets: [{
            label: 'Semester GPA',
            data: data.cgpa_progression.data,
            backgroundColor: '#6B1E2D',
            borderRadius: 4,
            barThickness: 26
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: '#555555' } },
            y: { min: 0, max: 10, grid: { color: '#E5E2DF' }, ticks: { color: '#555555' } }
          }
        }
      });
    }

    if (assignCanvas && data.assignment_status) {
      new Chart(assignCanvas.getContext('2d'), {
        type: 'pie',
        data: {
          labels: data.assignment_status.labels,
          datasets: [{
            data: data.assignment_status.data,
            backgroundColor: ['#28745A', '#A66A00', '#A33A3A'],
            borderWidth: 1,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
        }
      });
    }

    if (scatterCanvas && data.exam_scatter) {
      new Chart(scatterCanvas.getContext('2d'), {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Academic Correlation',
            data: data.exam_scatter.data,
            backgroundColor: '#6B1E2D',
            pointRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: 'Attendance %', color: '#555555' }, min: 50, max: 100 },
            y: { title: { display: true, text: 'GPA Standings', color: '#555555' }, min: 0, max: 10 }
          }
        }
      });
    }
  } catch (err) {
    console.error('Failed to load student chart data:', err);
    [attCanvas, cgpaCanvas, assignCanvas, scatterCanvas].forEach((canvas) => setChartState(canvas, 'error', 'Chart data could not be loaded.'));
  }
}

// --- Faculty Dashboard Charts ---
async function initFacultyCharts() {
  const attDistCanvas = document.getElementById('facultyAttendanceDistChart');
  const scoreDistCanvas = document.getElementById('facultyScoreDistChart');
  const supportPieCanvas = document.getElementById('facultySupportQueuePieChart');
  const interventionLineCanvas = document.getElementById('facultyInterventionLineChart');
  const clusteredBarCanvas = document.getElementById('facultySubjectClusteredBarChart');

  if (!attDistCanvas && !scoreDistCanvas && !supportPieCanvas && !interventionLineCanvas && !clusteredBarCanvas) return;

  try {
    [attDistCanvas, scoreDistCanvas, supportPieCanvas, interventionLineCanvas, clusteredBarCanvas].forEach((canvas) => setChartState(canvas, 'loading', 'Loading chart data...'));
    const res = await fetch('/faculty/api/charts');
    if (!res.ok) throw new Error('Unable to load faculty charts');
    const data = await res.json();

    if (attDistCanvas && data.attendance_dist) {
      new Chart(attDistCanvas.getContext('2d'), {
        type: 'doughnut',
        data: {
          labels: data.attendance_dist.labels,
          datasets: [{
            data: data.attendance_dist.data,
            backgroundColor: ['#28745A', '#A66A00', '#A33A3A'],
            borderWidth: 0
          }]
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '70%' }
      });
    }

    if (scoreDistCanvas && data.score_dist) {
      new Chart(scoreDistCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: data.score_dist.labels,
          datasets: [{
            label: 'Students Count',
            data: data.score_dist.data,
            backgroundColor: '#6B1E2D',
            borderRadius: 4,
            barThickness: 26
          }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });
    }

    if (supportPieCanvas && data.support_queue_dist) {
      new Chart(supportPieCanvas.getContext('2d'), {
        type: 'pie',
        data: {
          labels: data.support_queue_dist.labels,
          datasets: [{
            data: data.support_queue_dist.data,
            backgroundColor: ['#A33A3A', '#A66A00', '#28745A'],
            borderWidth: 1,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } }
        }
      });
    }

    if (interventionLineCanvas && data.intervention_trend) {
      new Chart(interventionLineCanvas.getContext('2d'), {
        type: 'line',
        data: {
          labels: data.intervention_trend.labels,
          datasets: [{
            label: 'Active Cases',
            data: data.intervention_trend.data,
            borderColor: '#A33A3A',
            backgroundColor: 'rgba(163, 58, 58, 0.08)',
            fill: true,
            tension: 0.35,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } }
        }
      });
    }

    if (clusteredBarCanvas && data.subject_averages) {
      new Chart(clusteredBarCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: data.subject_averages.labels,
          datasets: [
            {
              label: 'Class Avg',
              data: data.subject_averages.class_avg,
              backgroundColor: '#6B1E2D',
              borderRadius: 4
            },
            {
              label: 'Dept Avg',
              data: data.subject_averages.dept_avg,
              backgroundColor: '#A66A00',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
        }
      });
    }
  } catch (err) {
    console.error('Failed to load faculty chart data:', err);
    [attDistCanvas, scoreDistCanvas, supportPieCanvas, interventionLineCanvas, clusteredBarCanvas].forEach((canvas) => setChartState(canvas, 'error', 'Chart data could not be loaded.'));
  }
}

// --- Admin Dashboard Charts ---
async function initAdminCharts() {
  const deptCanvas = document.getElementById('adminDeptChart');
  const attDeptCanvas = document.getElementById('adminDeptAttChart');
  const riskPieCanvas = document.getElementById('adminRiskPieChart');
  const gpaAttScatterCanvas = document.getElementById('adminGpaAttScatterChart');
  const enrollPlacementClusteredCanvas = document.getElementById('adminEnrollPlacementClusteredChart');

  if (!deptCanvas && !attDeptCanvas && !riskPieCanvas && !gpaAttScatterCanvas && !enrollPlacementClusteredCanvas) return;

  try {
    [deptCanvas, attDeptCanvas, riskPieCanvas, gpaAttScatterCanvas, enrollPlacementClusteredCanvas].forEach((canvas) => setChartState(canvas, 'loading', 'Loading chart data...'));
    const res = await fetch('/admin/api/charts/dashboard');
    if (!res.ok) throw new Error('Unable to load admin charts');
    const data = await res.json();

    if (deptCanvas && data.department_students) {
      new Chart(deptCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: data.department_students.labels,
          datasets: [{
            label: 'Students Enrolled',
            data: data.department_students.data,
            backgroundColor: '#6B1E2D',
            borderRadius: 4,
            barThickness: 30
          }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });
    }

    if (attDeptCanvas && data.attendance_by_dept) {
      const ctx = attDeptCanvas.getContext('2d');
      const grad = ctx.createLinearGradient(0, 0, 0, 260);
      grad.addColorStop(0, 'rgba(40, 116, 90, 0.15)');
      grad.addColorStop(1, 'rgba(40, 116, 90, 0.0)');

      new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.attendance_by_dept.labels,
          datasets: [{
            label: 'Avg Attendance %',
            data: data.attendance_by_dept.data,
            borderColor: '#28745A',
            backgroundColor: grad,
            fill: true,
            tension: 0.35,
            borderWidth: 2.2
          }]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 50, max: 100 } } }
      });
    }

    if (riskPieCanvas && data.risk_dist) {
      new Chart(riskPieCanvas.getContext('2d'), {
        type: 'pie',
        data: {
          labels: data.risk_dist.labels,
          datasets: [{
            data: data.risk_dist.data,
            backgroundColor: ['#A33A3A', '#A66A00', '#28745A'],
            borderWidth: 1,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
        }
      });
    }

    if (gpaAttScatterCanvas && data.gpa_attendance_scatter) {
      new Chart(gpaAttScatterCanvas.getContext('2d'), {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Attendance vs CGPA Scatter',
            data: data.gpa_attendance_scatter.data,
            backgroundColor: '#28745A',
            pointRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: 'Attendance %', color: '#555555' }, min: 50, max: 100 },
            y: { title: { display: true, text: 'GPA Standings', color: '#555555' }, min: 0, max: 10 }
          }
        }
      });
    }

    if (enrollPlacementClusteredCanvas && data.enroll_placement) {
      new Chart(enrollPlacementClusteredCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: data.enroll_placement.labels,
          datasets: [
            {
              label: 'Admitted',
              data: data.enroll_placement.enrollments,
              backgroundColor: '#6B1E2D',
              borderRadius: 4
            },
            {
              label: 'Placed',
              data: data.enroll_placement.placements,
              backgroundColor: '#28745A',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
        }
      });
    }
  } catch (err) {
    console.error('Failed to load admin chart data:', err);
    [deptCanvas, attDeptCanvas, riskPieCanvas, gpaAttScatterCanvas, enrollPlacementClusteredCanvas].forEach((canvas) => setChartState(canvas, 'error', 'Chart data could not be loaded.'));
  }
}
