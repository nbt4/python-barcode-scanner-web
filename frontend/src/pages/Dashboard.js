import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Work as WorkIcon,
  QrCode as QrCodeIcon,
  Assessment as AssessmentIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import axios from '../config/axios';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    activeJobs: 0,
    totalDevices: 0,
    recentJobs: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch active jobs
        const jobsResponse = await axios.get('/api/v1/jobs', {
          params: {
            status: 'active',
            limit: 5,
          },
        });

        setStats({
          activeJobs: jobsResponse.data.length,
          recentJobs: jobsResponse.data,
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
            }}
            onClick={() => navigate('/jobs')}
          >
            <WorkIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6">Manage Jobs</Typography>
            <Typography variant="body2" color="text.secondary">
              Create or edit jobs
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
            }}
            onClick={() => navigate('/scanner')}
          >
            <QrCodeIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6">Scan Devices</Typography>
            <Typography variant="body2" color="text.secondary">
              Scan barcodes or QR codes
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
            }}
            onClick={() => navigate('/reports')}
          >
            <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6">Reports</Typography>
            <Typography variant="body2" color="text.secondary">
              Generate and view reports
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Jobs */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Recent Jobs
      </Typography>
      <Grid container spacing={3}>
        {stats.recentJobs.map((job) => (
          <Grid item xs={12} md={6} key={job.jobID}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job #{job.jobID}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  Customer: {job.kunde}
                </Typography>
                <Typography variant="body2">
                  Start Date: {new Date(job.startDate).toLocaleDateString('de-DE')}
                </Typography>
                <Typography variant="body2">
                  End Date: {new Date(job.endDate).toLocaleDateString('de-DE')}
                </Typography>
                <Typography variant="body2">
                  Devices: {job.device_count}
                </Typography>
                <Typography variant="body2" color="primary">
                  Status: {job.status}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate(`/jobs/${job.jobID}`)}
                >
                  View Details
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
        {stats.recentJobs.length === 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No recent jobs found
              </Typography>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

export default Dashboard;
