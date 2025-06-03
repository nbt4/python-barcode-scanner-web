import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  QrCode as QrCodeIcon,
  GetApp as DownloadIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import axios from '../config/axios';

function JobDetail() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openAddDevice, setOpenAddDevice] = useState(false);
  const [newDeviceId, setNewDeviceId] = useState('');
  const [customPrice, setCustomPrice] = useState('');

  const deviceColumns = [
    { field: 'deviceID', headerName: 'Device ID', width: 120 },
    { field: 'product', headerName: 'Product', width: 200 },
    {
      field: 'price',
      headerName: 'Price/Day',
      width: 120,
      valueFormatter: (params) => `€${params.value?.toFixed(2) || '0.00'}`,
    },
    {
      field: 'custom_price',
      headerName: 'Custom Price',
      width: 120,
      valueFormatter: (params) => 
        params.value ? `€${params.value.toFixed(2)}` : 'Default',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 200,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => generateQRCode(params.row.deviceID)}
            title="Generate QR Code"
          >
            <QrCodeIcon />
          </IconButton>
          <IconButton
            size="small"
            color="error"
            onClick={() => removeDevice(params.row.deviceID)}
            title="Remove Device"
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  useEffect(() => {
    fetchJobDetails();
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/jobs/${jobId}`);
      setJob(response.data);
      setDevices(response.data.devices || []);
      setError('');
    } catch (error) {
      console.error('Error fetching job details:', error);
      setError('Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  const addDevice = async () => {
    try {
      await axios.post(`/api/v1/devices/job/${jobId}/device`, {
        deviceID: newDeviceId,
        customPrice: customPrice ? parseFloat(customPrice) : null,
      });

      setOpenAddDevice(false);
      setNewDeviceId('');
      setCustomPrice('');
      fetchJobDetails(); // Refresh data
    } catch (error) {
      console.error('Error adding device:', error);
      if (error.response?.status === 400) {
        setError('Device is already in this job or not found');
      } else {
        setError('Failed to add device');
      }
    }
  };

  const removeDevice = async (deviceId) => {
    if (!window.confirm('Are you sure you want to remove this device from the job?')) {
      return;
    }

    try {
      await axios.delete(`/api/v1/devices/job/${jobId}/device/${deviceId}`);
      fetchJobDetails(); // Refresh data
    } catch (error) {
      console.error('Error removing device:', error);
      setError('Failed to remove device');
    }
  };

  const generateQRCode = async (deviceId) => {
    try {
      const response = await axios.get(`/api/v1/devices/qrcode/${deviceId}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `qr_device_${deviceId}.png`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating QR code:', error);
      setError('Failed to generate QR code');
    }
  };

  const generateJobReport = async () => {
    try {
      const response = await axios.get(`/api/v1/reports/job/${jobId}/devices`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `job_${jobId}_devices_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating report:', error);
      setError('Failed to generate report');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!job) {
    return (
      <Box>
        <Alert severity="error">Job not found</Alert>
      </Box>
    );
  }

  const totalRevenue = devices.reduce((sum, device) => sum + (device.price || 0), 0);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/jobs')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          Job #{job.jobID}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={generateJobReport}
          sx={{ mr: 2 }}
        >
          Download Report
        </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenAddDevice(true)}
        >
          Add Device
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Job Information */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Customer
                  </Typography>
                  <Typography variant="body1">
                    {job.kunde}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip 
                    label={job.status} 
                    color={job.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Start Date
                  </Typography>
                  <Typography variant="body1">
                    {job.startDate ? new Date(job.startDate).toLocaleDateString('de-DE') : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    End Date
                  </Typography>
                  <Typography variant="body1">
                    {job.endDate ? new Date(job.endDate).toLocaleDateString('de-DE') : 'N/A'}
                  </Typography>
                </Grid>
                {job.description && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Description
                    </Typography>
                    <Typography variant="body1">
                      {job.description}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Total Devices
                </Typography>
                <Typography variant="h4" color="primary">
                  {devices.length}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Daily Revenue
                </Typography>
                <Typography variant="h4" color="success.main">
                  €{totalRevenue.toFixed(2)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Devices Table */}
      <Paper sx={{ height: 400, width: '100%' }}>
        <Typography variant="h6" sx={{ p: 2 }}>
          Devices in Job
        </Typography>
        <DataGrid
          rows={devices}
          columns={deviceColumns}
          pageSize={10}
          rowsPerPageOptions={[10]}
          getRowId={(row) => row.deviceID}
          disableSelectionOnClick
        />
      </Paper>

      {/* Add Device Dialog */}
      <Dialog open={openAddDevice} onClose={() => setOpenAddDevice(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Device to Job</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Device ID"
                value={newDeviceId}
                onChange={(e) => setNewDeviceId(e.target.value)}
                helperText="Enter the device ID or scan a barcode"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Price (optional)"
                type="number"
                value={customPrice}
                onChange={(e) => setCustomPrice(e.target.value)}
                helperText="Leave empty to use default price"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDevice(false)}>Cancel</Button>
          <Button variant="contained" onClick={addDevice} disabled={!newDeviceId}>
            Add Device
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default JobDetail;
