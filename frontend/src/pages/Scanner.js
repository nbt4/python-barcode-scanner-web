import React, { useState, useRef, useCallback } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  IconButton,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import Webcam from 'react-webcam';
import jsQR from 'jsqr';
import axios from 'axios';

function Scanner() {
  const webcamRef = useRef(null);
  const [scanning, setScanning] = useState(false);
  const [scannedCode, setScannedCode] = useState('');
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [selectedJob, setSelectedJob] = useState('');
  const [customPrice, setCustomPrice] = useState('');
  const [jobs, setJobs] = useState([]);

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: 'environment' // Use back camera on mobile
  };

  const startScanning = () => {
    setScanning(true);
    setError('');
    setSuccess('');
    scanForCode();
  };

  const stopScanning = () => {
    setScanning(false);
  };

  const scanForCode = useCallback(() => {
    if (!scanning || !webcamRef.current) return;

    const video = webcamRef.current.video;
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
      setTimeout(scanForCode, 100);
      return;
    }

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);

    if (code) {
      setScannedCode(code.data);
      setScanning(false);
      verifyDevice(code.data);
    } else {
      setTimeout(scanForCode, 100);
    }
  }, [scanning]);

  const verifyDevice = async (deviceId) => {
    try {
      // Extract device ID from QR code if it has prefix
      const cleanDeviceId = deviceId.startsWith('DEVICE:') 
        ? deviceId.replace('DEVICE:', '') 
        : deviceId;

      const response = await axios.get(`/api/v1/devices/verify/${cleanDeviceId}`);
      
      if (response.data.valid) {
        setDeviceInfo(response.data.device);
        setError('');
        setSuccess(`Device ${cleanDeviceId} verified successfully!`);
      } else {
        setError('Device not found in database');
        setDeviceInfo(null);
      }
    } catch (error) {
      console.error('Error verifying device:', error);
      setError('Failed to verify device');
      setDeviceInfo(null);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await axios.get('/api/v1/jobs', {
        params: { status: 'active', limit: 50 }
      });
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleAddToJob = async () => {
    if (!selectedJob || !deviceInfo) return;

    try {
      await axios.post(`/api/v1/devices/job/${selectedJob}/device`, {
        deviceID: deviceInfo.deviceID,
        customPrice: customPrice ? parseFloat(customPrice) : null,
      });

      setSuccess(`Device ${deviceInfo.deviceID} added to job ${selectedJob} successfully!`);
      setOpenAddDialog(false);
      setSelectedJob('');
      setCustomPrice('');
      setDeviceInfo(null);
      setScannedCode('');
    } catch (error) {
      console.error('Error adding device to job:', error);
      if (error.response?.status === 400) {
        setError('Device is already in this job');
      } else {
        setError('Failed to add device to job');
      }
    }
  };

  const handleOpenAddDialog = () => {
    fetchJobs();
    setOpenAddDialog(true);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Device Scanner
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Camera Section */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Camera</Typography>
              <Box>
                {!scanning ? (
                  <Button
                    variant="contained"
                    startIcon={<CameraIcon />}
                    onClick={startScanning}
                  >
                    Start Scanning
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={stopScanning}
                  >
                    Stop Scanning
                  </Button>
                )}
              </Box>
            </Box>

            <Box sx={{ position: 'relative', width: '100%', maxWidth: 640, mx: 'auto' }}>
              <Webcam
                ref={webcamRef}
                audio={false}
                videoConstraints={videoConstraints}
                style={{
                  width: '100%',
                  height: 'auto',
                  border: scanning ? '3px solid #1976d2' : '1px solid #ccc',
                }}
              />
              {scanning && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 200,
                    height: 200,
                    border: '2px solid #1976d2',
                    borderRadius: 2,
                    pointerEvents: 'none',
                  }}
                />
              )}
            </Box>

            {scanning && (
              <Typography variant="body2" color="primary" sx={{ mt: 2, textAlign: 'center' }}>
                Position the barcode or QR code within the blue frame
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Scan Results
            </Typography>

            {scannedCode && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Scanned Code:
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  {scannedCode}
                </Typography>
              </Box>
            )}

            {deviceInfo && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="h6" color="primary">
                        Device Found
                      </Typography>
                      <Typography variant="body2">
                        <strong>ID:</strong> {deviceInfo.deviceID}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Product:</strong> {deviceInfo.name}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Price/Day:</strong> €{deviceInfo.itemcostperday?.toFixed(2) || '0.00'}
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setDeviceInfo(null);
                        setScannedCode('');
                      }}
                    >
                      <CloseIcon />
                    </IconButton>
                  </Box>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    fullWidth
                    sx={{ mt: 2 }}
                    onClick={handleOpenAddDialog}
                  >
                    Add to Job
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Manual Input */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Manual Device ID Entry:
              </Typography>
              <TextField
                fullWidth
                label="Device ID"
                value={scannedCode}
                onChange={(e) => setScannedCode(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && scannedCode) {
                    verifyDevice(scannedCode);
                  }
                }}
              />
              <Button
                variant="outlined"
                fullWidth
                sx={{ mt: 1 }}
                onClick={() => verifyDevice(scannedCode)}
                disabled={!scannedCode}
              >
                Verify Device
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Add to Job Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Device to Job</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Job</InputLabel>
                <Select
                  value={selectedJob}
                  label="Select Job"
                  onChange={(e) => setSelectedJob(e.target.value)}
                >
                  {jobs.map((job) => (
                    <MenuItem key={job.jobID} value={job.jobID}>
                      Job #{job.jobID} - {job.kunde}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Price (optional)"
                type="number"
                value={customPrice}
                onChange={(e) => setCustomPrice(e.target.value)}
                helperText={`Default price: €${deviceInfo?.itemcostperday?.toFixed(2) || '0.00'}/day`}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddToJob} disabled={!selectedJob}>
            Add to Job
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Scanner;
