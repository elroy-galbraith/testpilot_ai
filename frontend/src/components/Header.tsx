import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { AutoAwesome, Dashboard, Add, ViewList } from '@mui/icons-material';

const Header: React.FC = () => {
  const location = useLocation();

  return (
    <AppBar position="static">
      <Toolbar>
        <IconButton
          component={RouterLink}
          to="/"
          color="inherit"
          sx={{ mr: 1 }}
        >
          <AutoAwesome />
        </IconButton>
        <Typography 
          variant="h6" 
          component={RouterLink}
          to="/"
          sx={{ 
            flexGrow: 1, 
            textDecoration: 'none', 
            color: 'inherit',
            '&:hover': { opacity: 0.8 }
          }}
        >
          TestPilot AI
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button 
            color="inherit" 
            component={RouterLink} 
            to="/"
            startIcon={<Dashboard />}
            variant={location.pathname === '/' ? 'outlined' : 'text'}
            sx={{ 
              borderColor: location.pathname === '/' ? 'rgba(255,255,255,0.5)' : 'transparent',
              color: 'inherit'
            }}
          >
            Dashboard
          </Button>
          <Button 
            color="inherit" 
            component={RouterLink} 
            to="/tests"
            startIcon={<ViewList />}
            variant={location.pathname === '/tests' ? 'outlined' : 'text'}
            sx={{ 
              borderColor: location.pathname === '/tests' ? 'rgba(255,255,255,0.5)' : 'transparent',
              color: 'inherit'
            }}
          >
            All Tests
          </Button>
          <Button 
            color="inherit" 
            startIcon={<Add />}
            onClick={() => {
              // For now, show a coming soon message
              alert('🚧 New Test Creation UI coming soon!\n\nFor now, you can:\n• Use Slack: "/testpilot [your request]"\n• Use CLI: testpilot-cli generate "[your request]"');
            }}
          >
            New Test
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 