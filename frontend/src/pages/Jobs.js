import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  Grid,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useTheme,
  useMediaQuery,
  Card,
  CardContent,
  IconButton,
} from '@mui/material';
import { DataGrid, deDE } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import axios from 'axios';

function Jobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    dateFrom: null,
    dateTo: null,
  });

  // New job form
  const [newJob, setNewJob] = useState({
    customerID: '',
    statusID: '',
    startDate: null,
    endDate: null,
    description: '',
  });

  // Add these columns for the DataGrid
  const columns = [
    { 
      field: 'jobID', 
      headerName: 'Job ID', 
      width: 100,
      flex: 0.5,
    },
    {
      field: 'customerName',
      headerName: 'Customer',
      width: 200,
      flex: 1,
      renderCell: (params) => (
        <Typography noWrap>
          {`${params.row.companyname || ''} ${params.row.firstname || ''} ${params.row.lastname || ''}`}
        </Typography>
      ),
    },
    {
      field: 'description',
      headerName: 'Description',
      width: 300,
      flex: 1.5,
      renderCell: (params) => (
        <Typography noWrap>{params.row.description}</Typography>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      flex: 0.7,
      renderCell: (params) => (
        <Box
          sx={{
            backgroundColor: getStatusColor(params.row.status),
            color: '#fff',
            py: 0.5,
            px: 1.5,
            borderRadius: 1,
            fontSize: '0.875rem',
          }}
        >
          {params.row.status}
        </Box>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      flex: 0.7,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => navigate(`/jobs/${params.row.jobID}`)}
            sx={{ color: 'primary.main' }}
          >
            <EditIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return '#2e7d32'; // Green
      case 'completed':
        return '#1976d2'; // Blue
      case 'cancelled':
        return '#d32f2f'; // Red
      default:
        return '#757575'; // Grey
    }
  };

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const params = {
        search: filters.search,
        status: filters.status,
        date_from: filters.dateFrom?.toISOString().split('T')[0],
        date_to: filters.dateTo?.toISOString().split('T')[0],
      };

      const response = await axios.get('/api/v1/jobs', { params });
      setJobs(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setError('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const handleCreateJob = async () => {
    try {
      const response = await axios.post('/api/v1/jobs', {
        ...newJob,
        startDate: newJob.startDate?.toISOString().split('T')[0],
        endDate: newJob.endDate?.toISOString().split('T')[0],
      });

      setOpenDialog(false);
      setNewJob({
        customerID: '',
        statusID: '',
        startDate: null,
        endDate: null,
        description: '',
      });
      
      // Navigate to the new job's detail page
      navigate(`/jobs/${response.data.jobID}`);
    } catch (error) {
      console.error('Error creating job:', error);
      setError('Failed to create job');
    }
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      dateFrom: null,
      dateTo: null,
    });
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h4" component="h1" sx={{ color: 'primary.main', fontWeight: 500 }}>
          Jobs
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          sx={{
            bgcolor: 'primary.main',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
          }}
        >
          New Job
        </Button>
      </Box>

      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="Search"
              variant="outlined"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              InputProps={{
                startAdornment: <SearchIcon sx={{ color: 'action.active', mr: 1 }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                label="Status"
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="From Date"
              value={filters.dateFrom}
              onChange={(date) => setFilters({ ...filters, dateFrom: date })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="To Date"
              value={filters.dateTo}
              onChange={(date) => setFilters({ ...filters, dateTo: date })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ flexGrow: 1, height: { xs: 400, md: 600 } }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress />
          </Box>
        ) : (
          <DataGrid
            rows={jobs}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10, 25, 50]}
            getRowId={(row) => row.jobID}
            disableSelectionOnClick
            localeText={deDE.components.MuiDataGrid.defaultProps.localeText}
            sx={{
              '& .MuiDataGrid-cell': {
                cursor: 'pointer',
              },
              '& .MuiDataGrid-row:hover': {
                bgcolor: 'action.hover',
              },
            }}
            onRowClick={(params) => navigate(`/jobs/${params.row.jobID}`)}
          />
        )}
      </Paper>

      {/* Create Job Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Job</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Customer ID"
                value={newJob.customerID}
                onChange={(e) => setNewJob({ ...newJob, customerID: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={newJob.statusID}
                  label="Status"
                  onChange={(e) => setNewJob({ ...newJob, statusID: e.target.value })}
                >
                  <MenuItem value="1">Active</MenuItem>
                  <MenuItem value="2">Completed</MenuItem>
                  <MenuItem value="3">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Start Date"
                value={newJob.startDate}
                onChange={(date) => setNewJob({ ...newJob, startDate: date })}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="End Date"
                value={newJob.endDate}
                onChange={(date) => setNewJob({ ...newJob, endDate: date })}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={4}
                value={newJob.description}
                onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateJob}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Jobs;
