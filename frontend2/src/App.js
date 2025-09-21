 

// //import React, { useState } from 'react';
// import React, { useState, useEffect } from 'react';

// const FollowupQuestionsPopup = ({ 
//   sessionId, 
//   questions = [], 
//   onClose, 
//   onSubmit,
//   isOpen = true 
// }) => {
//   const [answers, setAnswers] = useState(Array(questions.length).fill(''));
//   const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
//   const [isSubmitting, setIsSubmitting] = useState(false);

//   const handleAnswerChange = (index, value) => {
//     const newAnswers = [...answers];
//     newAnswers[index] = value;
//     setAnswers(newAnswers);
//   };

//   const handleNext = () => {
//     if (currentQuestionIndex < questions.length - 1) {
//       setCurrentQuestionIndex(currentQuestionIndex + 1);
//     }
//   };

//   const handlePrevious = () => {
//     if (currentQuestionIndex > 0) {
//       setCurrentQuestionIndex(currentQuestionIndex - 1);
//     }
//   };

//   const handleSubmit = async () => {
//     const allAnswered = answers.every(answer => answer.trim());
//     if (!allAnswered) {
//       alert('Please answer all questions before submitting.');
//       return;
//     }

//     setIsSubmitting(true);
//     try {
//       await onSubmit(answers);
//       onClose();
//     } catch (error) {
//       console.error('Error submitting answers:', error);
//       alert('Failed to submit answers. Please try again.');
//     } finally {
//       setIsSubmitting(false);
//     }
//   };


// // ADD THIS SECTION - Authentication utility functions for LogBook JWT integration
// const AuthUtils = {
//   // Get JWT token from various possible locations
//   getToken: () => {
//     // Try localStorage first (most common for SPAs)
//     let token = localStorage.getItem('logbook_token') || localStorage.getItem('token');
    
//     // Try sessionStorage
//     if (!token) {
//       token = sessionStorage.getItem('logbook_token') || sessionStorage.getItem('token');
//     }
    
//     // Try cookies as fallback
//     if (!token) {
//       token = AuthUtils.getCookie('logbook_token');
//     }
    
//     return token;
//   },

//   // Get cookie by name
//   getCookie: (name) => {
//     const value = `; ${document.cookie}`;
//     const parts = value.split(`; ${name}=`);
//     if (parts.length === 2) return parts.pop().split(';').shift();
//     return null;
//   },

//   // Check if user is authenticated
//   isAuthenticated: () => {
//     const token = AuthUtils.getToken();
//     if (!token) return false;
    
//     try {
//       // Basic JWT validation - check if not expired
//       const payload = JSON.parse(atob(token.split('.')[1]));
//       const currentTime = Date.now() / 1000;
//       return payload.exp > currentTime;
//     } catch (error) {
//       console.error('Invalid token format:', error);
//       return false;
//     }
//   },

//   // Get authentication headers for API calls
//   getAuthHeaders: () => {
//     const token = AuthUtils.getToken();
    
//     if (!token) {
//       console.warn('No authentication token found');
//       // In real integration, redirect to LogBook login page
//       // window.location.href = '/login';
//       return {
//         'Content-Type': 'application/json',
//         'Accept': 'application/json'
//       };
//     }
    
//     return {
//       'Authorization': `Bearer ${token}`,
//       'Content-Type': 'application/json',
//       'Accept': 'application/json'
//     };
//   },

//   // Redirect to login (to be integrated with LogBook's login page)
//   redirectToLogin: () => {
//     console.log('Redirecting to LogBook login...');
//     // In real integration:
//     // window.location.href = '/login';
//     alert('Please log in through the LogBook system first.');
//   },

//   // Logout function
//   logout: () => {
//     localStorage.removeItem('logbook_token');
//     localStorage.removeItem('token');
//     sessionStorage.removeItem('logbook_token');
//     sessionStorage.removeItem('token');
//     // In real integration, also call LogBook logout endpoint
//     window.location.href = '/login';
//   }
// };

// // ADD THIS COMPONENT - Authentication Guard Component
// const AuthGuard = ({ children }) => {
//   const [isAuthenticated, setIsAuthenticated] = useState(false);
//   const [isChecking, setIsChecking] = useState(true);

//   useEffect(() => {
//     const checkAuth = () => {
//       const authenticated = AuthUtils.isAuthenticated();
//       setIsAuthenticated(authenticated);
//       setIsChecking(false);
      
//       if (!authenticated) {
//         console.log('User not authenticated, showing login prompt');
//       }
//     };

//     checkAuth();
    
//     // Check authentication status periodically
//     const interval = setInterval(checkAuth, 60000); // Check every minute
    
//     return () => clearInterval(interval);
//   }, []);

//   if (isChecking) {
//     return (
//       <div style={{
//         minHeight: '100vh',
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         backgroundColor: '#f5f7fa'
//       }}>
//         <div style={{ textAlign: 'center' }}>
//           <div style={{ 
//             fontSize: '24px', 
//             marginBottom: '16px',
//             color: '#2196F3'
//           }}>
//             🔐
//           </div>
//           <p style={{ color: '#666' }}>Checking authentication...</p>
//         </div>
//       </div>
//     );
//   }

//   if (!isAuthenticated) {
//     return (
//       <div style={{
//         minHeight: '100vh',
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         backgroundColor: '#f5f7fa'
//       }}>
//         <div style={{
//           backgroundColor: 'white',
//           borderRadius: '16px',
//           padding: '48px',
//           textAlign: 'center',
//           boxShadow: '0 8px 20px rgba(0,0,0,0.1)',
//           maxWidth: '400px',
//           width: '90%'
//         }}>
//           <div style={{
//             width: '80px',
//             height: '80px',
//             backgroundColor: '#ff9800',
//             borderRadius: '20px',
//             display: 'flex',
//             alignItems: 'center',
//             justifyContent: 'center',
//             margin: '0 auto 24px auto',
//             fontSize: '40px',
//             color: 'white'
//           }}>
//             🔐
//           </div>
          
//           <h2 style={{
//             color: '#333',
//             fontSize: '24px',
//             fontWeight: '600',
//             margin: '0 0 16px 0'
//           }}>
//             Authentication Required
//           </h2>
          
//           <p style={{
//             color: '#666',
//             fontSize: '16px',
//             lineHeight: '1.6',
//             margin: '0 0 32px 0'
//           }}>
//             Please log in through the LogBook system to access the Daily Activity Log.
//           </p>
          
//           <button
//             onClick={AuthUtils.redirectToLogin}
//             style={{
//               padding: '12px 32px',
//               backgroundColor: '#2196F3',
//               color: 'white',
//               border: 'none',
//               borderRadius: '8px',
//               cursor: 'pointer',
//               fontSize: '16px',
//               fontWeight: '600'
//             }}
//           >
//             Go to Login
//           </button>
//         </div>
//       </div>
//     );
//   }

//   return children;
// };
// //end new

//   const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
//   const answeredCount = answers.filter(answer => answer.trim()).length;

//   if (!isOpen || questions.length === 0) {
//     return null;
//   }

//   return (
//     <div style={{
//       position: 'fixed',
//       top: 0,
//       left: 0,
//       right: 0,
//       bottom: 0,
//       backgroundColor: 'rgba(0, 0, 0, 0.5)',
//       display: 'flex',
//       alignItems: 'center',
//       justifyContent: 'center',
//       zIndex: 1000
//     }}>
//       <div style={{
//         backgroundColor: 'white',
//         borderRadius: '8px',
//         padding: '32px',
//         width: '90%',
//         maxWidth: '600px',
//         maxHeight: '80vh',
//         overflow: 'auto'
//       }}>
//         {/* Header */}
//         <div style={{ 
//           display: 'flex', 
//           justifyContent: 'space-between', 
//           alignItems: 'center',
//           marginBottom: '24px'
//         }}>
//           <h2 style={{ 
//             margin: 0, 
//             fontSize: '24px',
//             fontWeight: 'bold',
//             color: '#333'
//           }}>
//             Follow-up Questions
//           </h2>
//           {/* <button
//             onClick={onClose}
//             style={{
//               background: 'none',
//               border: 'none',
//               fontSize: '24px',
//               cursor: 'pointer',
//               color: '#666'
//             }}
//           >
//             ×
//           </button> */}
//         </div>

//         {/* Progress Bar */}
//         <div style={{
//           backgroundColor: '#e0e0e0',
//           borderRadius: '10px',
//           height: '8px',
//           marginBottom: '16px'
//         }}>
//           <div
//             style={{
//               backgroundColor: '#4CAF50',
//               height: '100%',
//               borderRadius: '10px',
//               width: `${progress}%`,
//               transition: 'width 0.3s ease'
//             }}
//           />
//         </div>

//         <div style={{ 
//           textAlign: 'center',
//           marginBottom: '24px',
//           fontSize: '14px',
//           color: '#666'
//         }}>
//           Question {currentQuestionIndex + 1} of {questions.length} ({answeredCount} answered)
//         </div>

//         {/* Current Question */}
//         <div style={{ marginBottom: '24px' }}>
//           <h3 style={{
//             margin: '0 0 16px 0',
//             fontSize: '18px',
//             color: '#333'
//           }}>
//             {questions[currentQuestionIndex]}
//           </h3>
          
//           <textarea
//             value={answers[currentQuestionIndex]}
//             onChange={(e) => handleAnswerChange(currentQuestionIndex, e.target.value)}
//             placeholder="Type your answer here..."
//             rows={6}
//             style={{
//               width: '100%',
//               padding: '12px',
//               border: '1px solid #ccc',
//               borderRadius: '4px',
//               fontSize: '16px',
//               resize: 'vertical',
//               boxSizing: 'border-box'
//             }}
//           />
//         </div>

//         {/* Navigation */}
//         <div style={{
//           display: 'flex',
//           justifyContent: 'space-between',
//           alignItems: 'center'
//         }}>
//           <button
//             onClick={handlePrevious}
//             disabled={currentQuestionIndex === 0}
//             style={{
//               padding: '10px 20px',
//               backgroundColor: currentQuestionIndex === 0 ? '#f5f5f5' : '#fff',
//               color: currentQuestionIndex === 0 ? '#999' : '#333',
//               border: '1px solid #ccc',
//               borderRadius: '4px',
//               cursor: currentQuestionIndex === 0 ? 'not-allowed' : 'pointer'
//             }}
//           >
//             Previous
//           </button>

//           {currentQuestionIndex === questions.length - 1 ? (
//             <button
//               onClick={handleSubmit}
//               disabled={isSubmitting}
//               style={{
//                 padding: '10px 24px',
//                 backgroundColor: isSubmitting ? '#ccc' : '#4CAF50',
//                 color: 'white',
//                 border: 'none',
//                 borderRadius: '4px',
//                 cursor: isSubmitting ? 'not-allowed' : 'pointer',
//                 fontSize: '16px'
//               }}
//             >
//               {isSubmitting ? 'Submitting...' : 'Submit All Answers'}
//             </button>
//           ) : (
//             <button
//               onClick={handleNext}
//               style={{
//                 padding: '10px 20px',
//                 backgroundColor: '#2196F3',
//                 color: 'white',
//                 border: 'none',
//                 borderRadius: '4px',
//                 cursor: 'pointer'
//               }}
//             >
//               Next
//             </button>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// // Follow-up Redirect Screen Component
// const FollowupRedirectScreen = ({ 
//   userId, 
//   tempWorkUpdateId, 
//   onStartFollowup
// }) => {
//   const [isStarting, setIsStarting] = useState(false);

//   const handleStartFollowup = async () => {
//     setIsStarting(true);
//     try {
//       await onStartFollowup();
//     } catch (error) {
//       console.error('Error starting follow-up:', error);
//       alert('Failed to start follow-up session. Please try again.');
//     } finally {
//       setIsStarting(false);
//     }
//   };

//   return (
//     <div style={{
//       position: 'fixed',
//       top: 0,
//       left: 0,
//       right: 0,
//       bottom: 0,
//       backgroundColor: 'rgba(0, 0, 0, 0.5)',
//       display: 'flex',
//       alignItems: 'center',
//       justifyContent: 'center',
//       zIndex: 1000
//     }}>
//       <div style={{
//         backgroundColor: 'white',
//         borderRadius: '8px',
//         padding: '40px',
//         width: '50%',
//         maxWidth: '500px',
//         textAlign: 'center'
//       }}>
//         {/* Success Icon */}
//         {/* <div style={{
//           width: '60px',
//           height: '60px',
//           backgroundColor: '#2196F3',
//           borderRadius: '50%',
//           display: 'flex',
//           alignItems: 'center',
//           justifyContent: 'center',
//           margin: '0 auto 24px auto',
//           fontSize: '40px',
//           color: 'white'
//         }}>
          
//         </div> */}

        

//         <p style={{
//           color: '#666',
//           fontSize: '16px',
//           lineHeight: '1.5',
//           margin: '0 0 32px 0'
//         }}>
//           Please complete the required follow-up to submit your work update.
//         </p>

//         <button
//           onClick={handleStartFollowup}
//           disabled={isStarting}
//           style={{
//             padding: '12px 32px',
//             backgroundColor: isStarting ? '#ccc' : '#2196F3',
//             color: 'white',
//             border: 'none',
//             borderRadius: '4px',
//             cursor: isStarting ? 'not-allowed' : 'pointer',
//             fontSize: '16px',
//             fontWeight: 'bold'
//           }}
//         >
//           {isStarting ? 'Starting...' : "Let's Go"}
//         </button>
//       </div>
//     </div>
//   );
// };

// // ADD THIS - Available task stacks
// const taskStacks = [
//   'Frontend Development',
//   'Backend Development', 
//   'Mobile Development',
//   'DevOps & Infrastructure',
//   'UI/UX Design',
//   'Quality Assurance',
//   'Data Science',
//   'Machine Learning',
//   'Product Management',
//   'Business Analysis'
// ];


// // Main Work Update System Component
// const WorkUpdateSystem = () => {
//   //const [userId, setUserId] = useState('');
//   //const [workStatus, setWorkStatus] = useState('working'); // 'working', 'work from home', or 'onLeave'
//   //const [description, setDescription] = useState('');
//   const [status, setStatus] = useState('working'); // Change from workStatus
//   const [taskStack, setTaskStack] = useState(''); // ADD THIS
//   const [tasksCompleted, setTasksCompleted] = useState(''); // Change from description
//   const [challengesFaced, setChallengesFaced] = useState('');
//   const [plansForTomorrow, setPlansForTomorrow] = useState('');
  
//   // State for follow-up flow
//   const [showFollowupRedirect, setShowFollowupRedirect] = useState(false);
//   const [showFollowupQuestions, setShowFollowupQuestions] = useState(false);
//   const [tempWorkUpdateId, setTempWorkUpdateId] = useState(null); // Changed to temp ID
//   const [followupData, setFollowupData] = useState(null);

//   const handleSubmitWorkUpdate = async () => {
//     // Validation
//     if (!userId.trim()) {
//       alert('Please enter your User ID');
//       return;
//     }

//     // If working or work from home, require description. If on leave, description is optional
//     if ((workStatus === 'working' || workStatus === 'work from home') && !description.trim()) {
//       alert('Please enter your work description');
//       return;
//     }

//     try {
//       // Build payload based on work status
//       let workUpdateData;
      
//       if (workStatus === 'onLeave') {
//         // On leave submission - minimal data
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "on_leave",
//           "description": description.trim() || "On Leave",
//           "challenges": "",
//           "plans": ""
//         };
//       } else if (workStatus === 'work from home') {
//         // Work from home submission - treat as working
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "work_from_home",
//           "description": description.trim(),
//           "challenges": challengesFaced.trim() || "",
//           "plans": plansForTomorrow.trim() || ""
//         };
//       } else {
//         // Working submission - full data
//         workUpdateData = {
//           "userId": userId.trim(),
//           "work_status": "working",
//           "description": description.trim(),
//           "challenges": challengesFaced.trim() || "",
//           "plans": plansForTomorrow.trim() || ""
//         };
//       }

//       console.log('Submitting work update:', workUpdateData);

//       // STEP 1: Save work update only
//       const response = await fetch('http://localhost:8000/api/work-updates', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'Accept': 'application/json'
//         },
//         body: JSON.stringify(workUpdateData)
//       });

//       console.log('Response status:', response.status);

//       if (!response.ok) {
//         const errorText = await response.text();
//         console.error('Raw error response:', errorText);
//         throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
//       }

//       const result = await response.json();
//       console.log('Work update result:', result);

//       if (workStatus === 'onLeave') {
//         // On leave - work update saved permanently, no follow-up needed
//         alert('Your leave status has been submitted successfully!');
//         resetForm();
//       } else if (workStatus === 'working' || workStatus === 'work from home') {
//         // Working or work from home - work update saved to temp, need follow-up to finalize
//         setTempWorkUpdateId(result.tempWorkUpdateId);
//         setShowFollowupRedirect(true);
//       }

//     } catch (error) {
//       console.error('Error submitting work update:', error);
//       alert('Failed to submit work update: ' + error.message);
//     }
//   };

//   const handleStartFollowup = async () => {
//     try {
//       console.log('Starting follow-up session...');
      
//       // STEP 2: Start follow-up session (using temp work update ID)
//       const response = await fetch(`http://localhost:8000/api/followups/start?temp_work_update_id=${tempWorkUpdateId}&user_id=${userId}`, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         }
//       });

//       if (!response.ok) {
//         throw new Error(`HTTP error! status: ${response.status}`);
//       }

//       const result = await response.json();
//       console.log('Follow-up session started:', result);

//       // Set follow-up data and show questions popup
//       setFollowupData({
//         sessionId: result.sessionId,
//         questions: result.questions
//       });

//       // Hide redirect screen and show questions popup
//       setShowFollowupRedirect(false);
//       setShowFollowupQuestions(true);

//     } catch (error) {
//       console.error('Error starting follow-up:', error);
//       throw new Error('Failed to start follow-up session: ' + error.message);
//     }
//   };

//   const handleFollowupSubmit = async (answers) => {
//     try {
//       console.log('Submitting followup answers:', answers);
      
//       // Call your FastAPI backend to complete the follow-up session
//       const response = await fetch(`http://localhost:8000/api/followup/${followupData.sessionId}/complete`, {
//         method: 'PUT',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//           answers: answers
//         })
//       });

//       if (!response.ok) {
//         throw new Error(`HTTP error! status: ${response.status}`);
//       }

//       const result = await response.json();
//       console.log('Follow-up completed:', result);
      
//       alert('Follow-up questions completed successfully!');
      
//       // Reset form and close popups
//       resetForm();
//       setShowFollowupQuestions(false);
      
//     } catch (error) {
//       console.error('Error submitting followup:', error);
//       throw new Error('Failed to submit follow-up answers: ' + error.message);
//     }
//   };

//   const resetForm = () => {
//     setUserId('');
//     setDescription('');
//     setChallengesFaced('');
//     setPlansForTomorrow('');
//     setWorkStatus('working');
//     setTempWorkUpdateId(null); // Reset temp ID
//     setFollowupData(null);
//   };

//   const handleCloseFollowupRedirect = () => {
//     setShowFollowupRedirect(false);
//     resetForm();
//   };

//   const handleCloseFollowupQuestions = () => {
//     setShowFollowupQuestions(false);
//     resetForm();
//   };

//   return (
//     <div style={{
//       minHeight: '100vh',
//       backgroundColor: '#f5f5f5',
//       padding: '40px 20px'
//     }}>
//       <div style={{
//         maxWidth: '600px',
//         margin: '0 auto',
//         backgroundColor: 'white',
//         padding: '40px',
//         borderRadius: '8px',
//         boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
//       }}>
//         <div style={{ textAlign: 'center', marginBottom: '32px' }}>
//           <h1 style={{
//             fontSize: '36px',
//             fontWeight: 'bold',
//             color: '#4A90E2',
//             margin: '0 0 8px 0'
//           }}>
//             Work Update System
//           </h1>
//           <p style={{
//             color: '#666',
//             fontSize: '16px',
//             margin: 0
//           }}>
//             Submit your daily work update and answer follow-up questions
//           </p>
//         </div>

//         {/* User ID */}
//         <div style={{ marginBottom: '24px' }}>
//           <label style={{
//             display: 'block',
//             fontWeight: 'bold',
//             marginBottom: '8px',
//             color: '#333'
//           }}>
//             User ID *
//           </label>
//           <input
//             type="text"
//             value={userId}
//             onChange={(e) => setUserId(e.target.value)}
//             placeholder="Enter your user ID"
//             style={{
//               width: '100%',
//               padding: '12px',
//               border: '1px solid #ddd',
//               borderRadius: '4px',
//               fontSize: '16px',
//               boxSizing: 'border-box'
//             }}
//           />
//         </div>

//         {/* Work Status Radio Buttons */}
//         <div style={{ marginBottom: '24px' }}>
//           <label style={{
//             display: 'block',
//             fontWeight: 'bold',
//             marginBottom: '12px',
//             color: '#333'
//           }}>
//             Status *
//           </label>
//           <div style={{
//             display: 'flex',
//             gap: '20px',
//             marginBottom: '8px'
//           }}>
//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'working' ? '#4A90E2' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'working' ? '#f0f8ff' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="working"
//                 checked={workStatus === 'working'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'working' ? 'bold' : 'normal' }}>
//                 Working
//               </span>
//             </label>

//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'work from home' ? '#4A90E2' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'work from home' ? '#f0f8ff' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="work from home"
//                 checked={workStatus === 'work from home'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'work from home' ? 'bold' : 'normal' }}>
//                 Work From Home
//               </span>
//             </label>

//             <label style={{
//               display: 'flex',
//               alignItems: 'center',
//               cursor: 'pointer',
//               padding: '12px 16px',
//               border: '2px solid',
//               borderColor: workStatus === 'onLeave' ? '#FF9800' : '#ddd',
//               borderRadius: '8px',
//               backgroundColor: workStatus === 'onLeave' ? '#fff8e1' : 'white',
//               flex: 1,
//               textAlign: 'center'
//             }}>
//               <input
//                 type="radio"
//                 value="onLeave"
//                 checked={workStatus === 'onLeave'}
//                 onChange={(e) => setWorkStatus(e.target.value)}
//                 style={{ marginRight: '8px' }}
//               />
//               <span style={{ fontWeight: workStatus === 'onLeave' ? 'bold' : 'normal' }}>
//                 On Leave
//               </span>
//             </label>
//           </div>
//         </div>

//         {/* Work Description - Only show when working */}
//         {(workStatus === 'working' || workStatus === 'work from home') && (
//           <div style={{ marginBottom: '24px' }}>
//             <label style={{
//               display: 'block',
//               fontWeight: 'bold',
//               marginBottom: '8px',
//               color: '#333'
//             }}>
//               Work Description *
//             </label>
//             <textarea
//               value={description}
//               onChange={(e) => setDescription(e.target.value)}
//               placeholder="What did you accomplish today? Be specific..."
//               rows={4}
//               style={{
//                 width: '100%',
//                 padding: '12px',
//                 border: '1px solid #ddd',
//                 borderRadius: '4px',
//                 fontSize: '16px',
//                 resize: 'vertical',
//                 boxSizing: 'border-box'
//               }}
//             />
//           </div>
//         )}

//         {/* Show additional fields only when working */}
//         {(workStatus === 'working' || workStatus === 'work from home') && (
//           <>
//             {/* Challenges Faced - Optional */}
//             <div style={{ marginBottom: '24px' }}>
//               <label style={{
//                 display: 'block',
//                 fontWeight: 'bold',
//                 marginBottom: '8px',
//                 color: '#333'
//               }}>
//                 Challenges Faced
//               </label>
//               <textarea
//                 value={challengesFaced}
//                 onChange={(e) => setChallengesFaced(e.target.value)}
//                 placeholder="Any challenges or difficulties you encountered..."
//                 rows={3}
//                 style={{
//                   width: '100%',
//                   padding: '12px',
//                   border: '1px solid #ddd',
//                   borderRadius: '4px',
//                   fontSize: '16px',
//                   resize: 'vertical',
//                   boxSizing: 'border-box'
//                 }}
//               />
//             </div>

//             {/* Plans for Tomorrow - Optional */}
//             <div style={{ marginBottom: '32px' }}>
//               <label style={{
//                 display: 'block',
//                 fontWeight: 'bold',
//                 marginBottom: '8px',
//                 color: '#333'
//               }}>
//                 Plans for Tomorrow
//               </label>
//               <textarea
//                 value={plansForTomorrow}
//                 onChange={(e) => setPlansForTomorrow(e.target.value)}
//                 placeholder="What will you focus on tomorrow..."
//                 rows={3}
//                 style={{
//                   width: '100%',
//                   padding: '12px',
//                   border: '1px solid #ddd',
//                   borderRadius: '4px',
//                   fontSize: '16px',
//                   resize: 'vertical',
//                   boxSizing: 'border-box'
//                 }}
//               />
//             </div>
//           </>
//         )}

//         {/* Submit Button */}
//         <button
//           onClick={handleSubmitWorkUpdate}
//           style={{
//             width: '100%',
//             padding: '16px',
//             backgroundColor: workStatus === 'onLeave' ? '#FF9800' : '#4A90E2',
//             color: 'white',
//             border: 'none',
//             borderRadius: '4px',
//             fontSize: '18px',
//             fontWeight: 'bold',
//             cursor: 'pointer'
//           }}
//         >
//           {workStatus === 'onLeave' ? 'Submit Leave Status' : 'Submit Work Update'}
//         </button>

//         {/* Status indicator */}
//         {workStatus === 'onLeave' && (
//           <div style={{
//             marginTop: '16px',
//             padding: '12px',
//             backgroundColor: '#fff3cd',
//             border: '1px solid #ffeaa7',
//             borderRadius: '4px',
//             color: '#856404',
//             fontSize: '14px',
//             textAlign: 'center'
//           }}>
//             ℹ️ No further details needed for leave days
//           </div>
//         )}
//       </div>

//       {/* Follow-up Redirect Screen */}
//       {showFollowupRedirect && (
//         <FollowupRedirectScreen
//           userId={userId}
//           tempWorkUpdateId={tempWorkUpdateId}
//           onStartFollowup={handleStartFollowup}
//         />
//       )}

//       {/* Follow-up Questions Popup */}
//       {showFollowupQuestions && followupData && (
//         <FollowupQuestionsPopup
//           sessionId={followupData.sessionId}
//           questions={followupData.questions}
//           isOpen={showFollowupQuestions}
//           onClose={handleCloseFollowupQuestions}
//           onSubmit={handleFollowupSubmit}
//         />
//       )}
//     </div>
//   );
// };

// export default WorkUpdateSystem;




import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Modal Component for Follow-up Questions
const FollowupModal = ({ isOpen, onClose, onComplete, questions, sessionId, userId }) => {
  const [answers, setAnswers] = useState(['', '', '']);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnswerChange = (value) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = value;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = async () => {
    if (answers.some(answer => !answer.trim())) {
      alert('Please answer all questions before submitting.');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/followup/${sessionId}/complete`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          answers: answers
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        onComplete(data);
        onClose();
      } else {
        alert(data.message || 'Failed to submit follow-up answers');
      }
    } catch (error) {
      console.error('Error submitting follow-up:', error);
      alert('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>AI Follow-up Questions</h2>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="progress-text">Question {currentQuestionIndex + 1} of {questions.length}</p>
        </div>

        <div className="question-container">
          <h3>{questions[currentQuestionIndex]}</h3>
          <textarea
            value={answers[currentQuestionIndex]}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Type your answer here..."
            rows="6"
            className="question-textarea"
          />
        </div>

        <div className="modal-buttons">
          <button 
            onClick={handlePrevious} 
            disabled={currentQuestionIndex === 0}
            className="btn-secondary"
          >
            Previous
          </button>
          
          {currentQuestionIndex < questions.length - 1 ? (
            <button 
              onClick={handleNext}
              disabled={!answers[currentQuestionIndex].trim()}
              className="btn-primary"
            >
              Next
            </button>
          ) : (
            <button 
              onClick={handleSubmit}
              disabled={!answers[currentQuestionIndex].trim() || isSubmitting}
              className="btn-primary"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Answers'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [formData, setFormData] = useState({
    user_id: '',
    status: 'working',
    stack: '',
    task: '',
    progress: '',
    blockers: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFollowup, setShowFollowup] = useState(false);
  const [followupData, setFollowupData] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  const stackOptions = [
    'Frontend Development',
    'Backend Development',
    'Full Stack Development',
    'Mobile Development',
    'DevOps',
    'Data Science',
    'UI/UX Design',
    'Quality Assurance',
    'Other'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'status' && value === 'leave') {
      // Clear task-related fields when switching to leave
      setFormData(prev => ({
        ...prev,
        [name]: value,
        stack: '',
        task: '',
        progress: '',
        blockers: ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async () => {
    
    if (!formData.user_id.trim()) {
      setMessage('User ID is required');
      setMessageType('error');
      return;
    }

    // Only validate task when not on leave
    if ((formData.status === 'working' || formData.status === 'wfh') && !formData.task.trim()) {
      setMessage('Task description is required when working');
      setMessageType('error');
      return;
    }

    // Only validate stack when not on leave
    if (formData.status !== 'leave' && !formData.stack.trim()) {
      setMessage('Please select your task stack');
      setMessageType('error');
      return;
    }

    setIsSubmitting(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/work-updates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        if (data.redirectToFollowup) {
          // Start follow-up session
          await startFollowupSession(data);
        } else {
          setMessage(data.message);
          setMessageType('success');
          // Reset form after successful submission
          setFormData({
            user_id: formData.user_id, // Keep user_id
            status: 'working',
            stack: '',
            task: '',
            progress: '',
            blockers: ''
          });
        }
      } else {
        setMessage(data.message || 'Submission failed');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Error submitting work update:', error);
      setMessage('Network error. Please try again.');
      setMessageType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const startFollowupSession = async (workUpdateData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/followups/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: formData.user_id
        }),
      });

      const data = await response.json();

      if (data.success) {
        setFollowupData(data);
        setShowFollowup(true);
        setMessage(`Quality Score: ${workUpdateData.qualityScore}/10. Please complete follow-up questions.`);
        setMessageType('info');
      } else {
        setMessage(data.message || 'Failed to start follow-up session');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Error starting follow-up:', error);
      setMessage('Failed to start follow-up session');
      setMessageType('error');
    }
  };

  const handleFollowupComplete = (data) => {
    setMessage(`Follow-up completed successfully! Your work update has been saved to the LogBook system.`);
    setMessageType('success');
    setFollowupData(null);
    
    // Reset form
    setFormData({
      user_id: formData.user_id, // Keep user_id
      status: 'working',
      stack: '',
      task: '',
      progress: '',
      blockers: ''
    });
  };

  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
            'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
            sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .app {
          min-height: 100vh;
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .container {
          background: white;
          border-radius: 20px;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
          max-width: 800px;
          width: 100%;
          overflow: hidden;
        }

        .header {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          padding: 30px;
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .header-icon {
          font-size: 3rem;
          background: rgba(255, 255, 255, 0.2);
          padding: 15px;
          border-radius: 15px;
          backdrop-filter: blur(10px);
        }

        .header h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 5px;
        }

        .header p {
          opacity: 0.9;
          font-size: 1rem;
        }

        .message {
          margin: 20px 30px;
          padding: 15px 20px;
          border-radius: 10px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .message-success {
          background: #dcfce7;
          color: #166534;
          border-left: 4px solid #22c55e;
        }

        .message-error {
          background: #fef2f2;
          color: #dc2626;
          border-left: 4px solid #ef4444;
        }

        .message-info {
          background: #dbeafe;
          color: #1d4ed8;
          border-left: 4px solid #3b82f6;
        }

        .work-form {
          padding: 30px;
        }

        .form-group {
          margin-bottom: 25px;
          transition: all 0.3s ease;
        }

        .form-group.hidden {
          opacity: 0;
          max-height: 0;
          margin: 0;
          padding: 0;
          overflow: hidden;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 600;
          color: #374151;
          font-size: 0.95rem;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 10px;
          font-size: 1rem;
          transition: all 0.2s ease;
          background: #fafafa;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #3b82f6;
          background: white;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .form-group textarea {
          resize: vertical;
          min-height: 100px;
          font-family: inherit;
          line-height: 1.5;
        }

        .radio-group {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
          margin-top: 8px;
        }

        .radio-option {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          padding: 12px 20px;
          border: 2px solid #e5e7eb;
          border-radius: 10px;
          background: #fafafa;
          transition: all 0.2s ease;
          font-weight: 500;
        }

        .radio-option:hover {
          border-color: #3b82f6;
          background: #f0f9ff;
        }

        .radio-option input[type="radio"] {
          width: auto;
          margin: 0;
          accent-color: #3b82f6;
        }

        .radio-option input[type="radio"]:checked + span {
          color: #1d4ed8;
        }

        .radio-option:has(input[type="radio"]:checked) {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .submit-btn {
          width: 100%;
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          border: none;
          padding: 16px 24px;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        }

        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .info-note {
          background: #f0f9ff;
          border: 1px solid #bae6fd;
          border-radius: 10px;
          padding: 15px;
          margin-top: 20px;
          display: flex;
          align-items: center;
          gap: 10px;
          color: #0369a1;
          font-size: 0.9rem;
        }

        .info-icon {
          font-size: 1.2rem;
        }

        .footer {
          background: #f8fafc;
          padding: 20px 30px;
          text-align: center;
          color: #64748b;
          font-size: 0.85rem;
          border-top: 1px solid #e2e8f0;
        }

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: white;
          border-radius: 20px;
          max-width: 600px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
        }

        .modal-header {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          padding: 25px;
          border-radius: 20px 20px 0 0;
        }

        .modal-header h2 {
          font-size: 1.5rem;
          margin-bottom: 15px;
          font-weight: 700;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 10px;
        }

        .progress-fill {
          height: 100%;
          background: white;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .progress-text {
          font-size: 0.9rem;
          opacity: 0.9;
        }

        .question-container {
          padding: 30px;
        }

        .question-container h3 {
          font-size: 1.2rem;
          color: #374151;
          margin-bottom: 20px;
          line-height: 1.4;
        }

        .question-textarea {
          width: 100%;
          min-height: 150px;
          padding: 15px;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          font-size: 1rem;
          font-family: inherit;
          line-height: 1.6;
          resize: vertical;
          transition: all 0.2s ease;
        }

        .question-textarea:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .modal-buttons {
          padding: 20px 30px;
          display: flex;
          gap: 15px;
          justify-content: space-between;
          border-top: 1px solid #e5e7eb;
        }

        .btn-primary {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 120px;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .btn-secondary {
          background: #f8fafc;
          color: #64748b;
          border: 2px solid #e2e8f0;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 120px;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #e2e8f0;
          border-color: #cbd5e1;
        }

        .btn-secondary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .app {
            padding: 10px;
          }
          
          .container {
            margin: 0;
            border-radius: 15px;
          }
          
          .header {
            padding: 20px;
            flex-direction: column;
            text-align: center;
          }
          
          .header-icon {
            font-size: 2.5rem;
            padding: 12px;
          }
          
          .work-form {
            padding: 20px;
          }
          
          .radio-group {
            flex-direction: column;
            gap: 10px;
          }
          
          .radio-option {
            justify-content: center;
          }
          
          .modal-content {
            margin: 10px;
            max-height: calc(100vh - 20px);
          }
          
          .modal-buttons {
            flex-direction: column;
          }
          
          .btn-primary,
          .btn-secondary {
            width: 100%;
          }
        }

        /* Animation for success states */
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .message {
          animation: fadeInScale 0.3s ease-out;
        }

        /* Loading spinner for buttons */
        .submit-btn:disabled::after {
          content: '';
          display: inline-block;
          width: 20px;
          height: 20px;
          margin-left: 10px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
      
      <div className="app">
        <div className="container">
          <div className="header">
            <div className="header-icon">📊</div>
            <div>
              <h1>Daily Activity Log</h1>
              <p>Complete your daily work summary with AI-powered follow-up</p>
            </div>
          </div>

          {message && (
            <div className={`message message-${messageType}`}>
              {message}
            </div>
          )}

          <div className="work-form">
            <div className="form-group">
              <label htmlFor="user_id">User ID *</label>
              <input
                type="text"
                id="user_id"
                name="user_id"
                value={formData.user_id}
                onChange={handleInputChange}
                placeholder="Enter your user ID (e.g., intern123)"
                required
              />
            </div>

            <div className="form-group">
              <label>Status *</label>
              <div className="radio-group">
                <label className="radio-option">
                  <input
                    type="radio"
                    name="status"
                    value="working"
                    checked={formData.status === 'working'}
                    onChange={handleInputChange}
                  />
                  <span>Working</span>
                </label>
                <label className="radio-option">
                  <input
                    type="radio"
                    name="status"
                    value="wfh"
                    checked={formData.status === 'wfh'}
                    onChange={handleInputChange}
                  />
                  <span>Work From Home</span>
                </label>
                <label className="radio-option">
                  <input
                    type="radio"
                    name="status"
                    value="leave"
                    checked={formData.status === 'leave'}
                    onChange={handleInputChange}
                  />
                  <span>On Leave</span>
                </label>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="stack">Task Stack *</label>
              <select
                id="stack"
                name="stack"
                value={formData.stack}
                onChange={handleInputChange}
                required={formData.status !== 'leave'}
                style={{ display: formData.status === 'leave' ? 'none' : 'block' }}
              >
                <option value="">Select your stack...</option>
                {stackOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
              <label htmlFor="task">Tasks Completed *</label>
              <textarea
                id="task"
                name="task"
                value={formData.task}
                onChange={handleInputChange}
                placeholder="What did you accomplish today? Be specific about tasks completed, features implemented, bugs fixed, etc..."
                rows="4"
                required={formData.status !== 'leave'}
              />
            </div>

            <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
              <label htmlFor="progress">Challenges Faced</label>
              <textarea
                id="progress"
                name="progress"
                value={formData.progress}
                onChange={handleInputChange}
                placeholder="Any obstacles, technical issues, or difficulties you encountered today..."
                rows="3"
              />
            </div>

            <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
              <label htmlFor="blockers">Plans for Tomorrow</label>
              <textarea
                id="blockers"
                name="blockers"
                value={formData.blockers}
                onChange={handleInputChange}
                placeholder="What tasks will you focus on tomorrow? Any specific goals or priorities..."
                rows="3"
              />
            </div>

            <button type="button" onClick={handleSubmit} disabled={isSubmitting} className="submit-btn">
              {isSubmitting ? 'Submitting...' : 'Submit Logbook'}
            </button>

            {formData.status !== 'leave' && (
              <div className="info-note">
                <span className="info-icon">🤖</span>
                AI follow-up questions will be generated after submission to ensure quality
              </div>
            )}
          </div>

          <footer className="footer">
            Powered by TalentHub LogBook System with AI Enhancement | Your data is secure and only accessible to authorized supervisors
          </footer>
        </div>

        <FollowupModal
          isOpen={showFollowup}
          onClose={() => setShowFollowup(false)}
          onComplete={handleFollowupComplete}
          questions={followupData?.questions || []}
          sessionId={followupData?.sessionId}
          userId={formData.user_id}
        />
      </div>
    </>
  );
};

export default App;