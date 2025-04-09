import React, { useEffect } from 'react';

const MobileMenu = () => {
  const toggleMenu = () => {
    const sideNav = document.querySelector('.side-nav');
    const menuOverlay = document.querySelector('.menu-overlay');
    
    if (sideNav) {
      sideNav.classList.toggle('active');
    }
    
    if (menuOverlay) {
      menuOverlay.classList.toggle('active');
    }
  };
  
  const closeMenuOnResize = () => {
    const sideNav = document.querySelector('.side-nav');
    const menuOverlay = document.querySelector('.menu-overlay');
    
    if (window.innerWidth > 992) {
      if (sideNav) sideNav.classList.remove('active');
      if (menuOverlay) menuOverlay.classList.remove('active');
    }
  };
  
  const closeMenuOnOutsideClick = (e) => {
    if (e.target.classList.contains('menu-overlay')) {
      toggleMenu();
    }
  };
  
  useEffect(() => {
    window.addEventListener('resize', closeMenuOnResize);
    document.addEventListener('click', closeMenuOnOutsideClick);
    
    return () => {
      window.removeEventListener('resize', closeMenuOnResize);
      document.removeEventListener('click', closeMenuOnOutsideClick);
    };
  }, []);
  
  return (
    <>
      <button className="mobile-menu-toggle" onClick={toggleMenu}>
        <i className="fas fa-bars"></i>
      </button>
      <div className="menu-overlay"></div>
    </>
  );
};

export default MobileMenu;
