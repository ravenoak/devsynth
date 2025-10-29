---
author: DevSynth Team
date: '2025-07-10'
last_reviewed: "2025-07-10"
status: published
tags:
- architecture
- webui
- ux
- nicegui
- interface
- responsive design
- styling
- error handling

title: WebUI Implementation Details
version: "0.1.0a1"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; WebUI Implementation Details
</div>

# WebUI Implementation Details

## Introduction

This document provides detailed information about the implementation of the DevSynth WebUI, focusing on responsive design, consistent styling, and enhanced error handling. These features were implemented as part of Phase 4 of the DevSynth [Release Plan](../roadmap/release_plan.md).

## Responsive Design

The WebUI implements responsive design to adapt to different screen sizes, ensuring a good user experience on devices ranging from mobile phones to desktop computers.

### Screen Size Detection

The WebUI uses JavaScript to detect the screen width and store it in the session state:

```javascript
// Function to update screen width in session state
function updateScreenWidth() {
    const width = window.innerWidth;
    const data = {
        width: width,
        height: window.innerHeight
    };

    // Use NiceGUI's setComponentValue to update session state
    if (window.parent.nicegui) {
        window.parent.nicegui.setComponentValue(data);
    }
}

// Update on page load
updateScreenWidth();

// Update on window resize
window.addEventListener('resize', updateScreenWidth);
```

This JavaScript code is injected into the page using NiceGUI's `st.components.v1.html` function, allowing the WebUI to respond to changes in the browser window size.

### Layout Configuration

The WebUI uses a `get_layout_config` method to return layout configuration parameters based on the screen width:

```python
def get_layout_config(self) -> dict:
    """Get layout configuration based on screen size.

    Returns:
        A dictionary with layout configuration parameters.
    """
    # Get screen width from session state or use default
    screen_width = getattr(st.session_state, "screen_width", 1200)

    # Define layout configurations for different screen sizes
    if screen_width < 768:  # Mobile
        return {
            "columns": 1,
            "sidebar_width": "100%",
            "content_width": "100%",
            "font_size": "small",
            "padding": "0.5rem",
            "is_mobile": True
        }
    elif screen_width < 992:  # Tablet
        return {
            "columns": 2,
            "sidebar_width": "30%",
            "content_width": "70%",
            "font_size": "medium",
            "padding": "1rem",
            "is_mobile": False
        }
    else:  # Desktop
        return {
            "columns": 3,
            "sidebar_width": "20%",
            "content_width": "80%",
            "font_size": "medium",
            "padding": "1.5rem",
            "is_mobile": False
        }
```

This method returns different layout configurations for mobile (< 768px), tablet (< 992px), and desktop (≥ 992px) screens, including parameters for the number of columns, sidebar width, content width, font size, padding, and a flag indicating if it's a mobile device.

### Applying Responsive Layout

The layout configuration is applied in the `run` method of the WebUI class:

```python
def run(self) -> None:
    """Run the NiceGUI application."""
    st.set_page_config(page_title="DevSynth WebUI", layout="wide")

    # Get screen dimensions from component value
    if "screen_width" not in st.session_state:
        st.session_state.screen_width = 1200
        st.session_state.screen_height = 800

    # Apply layout configuration based on screen size
    layout_config = self.get_layout_config()

    # Apply custom CSS for responsive layout
    custom_css = f"""
    <style>
        .main .block-container {{
            padding: {layout_config["padding"]};
        }}
        .stSidebar .sidebar-content {{
            width: {layout_config["sidebar_width"]};
        }}
        .main {{
            font-size: {layout_config["font_size"]};
        }}
        /* Other CSS rules... */
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Rest of the run method...
```

This code applies the layout configuration by injecting custom CSS into the page, which adjusts the padding, sidebar width, and font size based on the screen size.

## Consistent Styling and Branding

The WebUI implements consistent styling and branding to provide a cohesive user experience across all pages.

### Branding Colors

The WebUI defines a set of branding colors that are used consistently throughout the interface:

```css
/* DevSynth branding colors */
.devsynth-primary {
    color: #4A90E2;
}
.devsynth-secondary {
    color: #50E3C2;
}
.devsynth-accent {
    color: #F5A623;
}
.devsynth-error {
    color: #D0021B;
}
.devsynth-success {
    color: #7ED321;
}
.devsynth-warning {
    color: #F8E71C;
}
```

These colors are used for various UI elements, including text, buttons, and status indicators.

### Form Styling

The WebUI applies consistent styling to forms:

```css
/* Consistent form styling */
.stForm {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
}
```

This ensures that all forms have the same appearance, with a light gray background, rounded corners, and consistent padding.

### Button Styling

The WebUI applies consistent styling to buttons:

```css
/* Consistent button styling */
.stButton>button {
    background-color: #4A90E2;
    color: white;
    border-radius: 4px;
    border: none;
    padding: 0.5rem 1rem;
}
.stButton>button:hover {
    background-color: #3A80D2;
}
```

This ensures that all buttons have the same appearance, with a blue background, white text, rounded corners, and a hover effect.

### Branding Elements

The WebUI includes branding elements in the sidebar:

```python
# Apply branding
st.sidebar.title("DevSynth")
st.sidebar.markdown(
    '<div class="devsynth-secondary" style="font-size: 0.8rem; margin-bottom: 2rem;">Intelligent Software Development</div>',
    unsafe_allow_html=True
)
```

This adds the DevSynth title and tagline to the sidebar, using the branding colors.

## Enhanced Error Handling

The WebUI implements enhanced error handling to provide detailed error messages with suggestions and documentation links.

### Error Type Detection

The WebUI includes a method to extract the error type from an error message:

```python
def _get_error_type(self, message: str) -> str:
    """Extract the error type from an error message.

    Args:
        message: The error message

    Returns:
        The error type, or an empty string if no type could be determined
    """
    if "File not found" in message:
        return "file_not_found"
    elif "Permission denied" in message:
        return "permission_denied"
    elif "Invalid parameter" in message:
        return "invalid_parameter"
    elif "Invalid format" in message:
        return "invalid_format"
    elif "Configuration error" in message:
        return "config_error"
    elif "Connection error" in message:
        return "connection_error"
    elif "API error" in message:
        return "api_error"
    elif "Validation error" in message:
        return "validation_error"
    elif "Syntax error" in message:
        return "syntax_error"
    elif "Import error" in message:
        return "import_error"
    else:
        return ""
```

This method analyzes the error message to determine the type of error, which is used to provide specific suggestions and documentation links.

### Error Suggestions

The WebUI includes a method to get suggestions for fixing an error based on its type:

```python
def _get_error_suggestions(self, error_type: str) -> list[str]:
    """Get suggestions for fixing an error.

    Args:
        error_type: The type of error

    Returns:
        A list of suggestions
    """
    suggestions = {
        "file_not_found": [
            "Check that the file path is correct",
            "Verify that the file exists in the specified location",
            "If using a relative path, make sure you're in the correct directory"
        ],
        "permission_denied": [
            "Check that you have the necessary permissions to access the file",
            "Try running the command with elevated privileges",
            "Verify that the file is not locked by another process"
        ],
        # Other error types...
    }

    return suggestions.get(error_type, [])
```

This method returns a list of suggestions for fixing the error based on its type, providing actionable information to the user.

### Documentation Links

The WebUI includes a method to get documentation links for an error based on its type:

```python
def _get_documentation_links(self, error_type: str) -> dict[str, str]:
    """Get documentation links for an error.

    Args:
        error_type: The type of error

    Returns:
        A dictionary mapping link titles to URLs
    """
    base_url = "https://devsynth.readthedocs.io/en/latest"
    links = {
        "file_not_found": {
            "File Handling Guide": f"{base_url}/user_guides/file_handling.html",
            "Common File Errors": f"{base_url}/user_guides/troubleshooting.html#file-errors"
        },
        "permission_denied": {
            "Permission Issues": f"{base_url}/user_guides/troubleshooting.html#permission-issues",
            "Security Configuration": f"{base_url}/user_guides/security_config.html"
        },
        # Other error types...
    }

    return links.get(error_type, {})
```

This method returns a dictionary mapping link titles to URLs for documentation related to the error type, providing additional resources to help the user resolve the issue.

### Enhanced Error Display

The WebUI enhances the display of error messages in the `display_result` method:

```python
def display_result(self, message: str, *, highlight: bool = False) -> None:
    """Display a message to the user with appropriate styling.

    Args:
        message: The message to display
        highlight: Whether to highlight the message
    """
    message = sanitize_output(message)

    # Process Rich markup in the message if present
    if "[" in message and "]" in message:
        # Convert Rich markup to Markdown
        # ...
        st.markdown(message, unsafe_allow_html=True)
        return

    # Apply appropriate styling based on message content and highlight flag
    if highlight:
        st.info(message)
    elif message.startswith("ERROR") or message.startswith("FAILED"):
        # Display error message
        st.error(message)

        # Add suggestions and documentation links for common errors
        error_type = self._get_error_type(message)
        if error_type:
            # Add suggestions
            suggestions = self._get_error_suggestions(error_type)
            if suggestions:
                st.markdown("**Suggestions:**")
                for suggestion in suggestions:
                    st.markdown(f"- {suggestion}")

            # Add documentation links
            doc_links = self._get_documentation_links(error_type)
            if doc_links:
                st.markdown("**Documentation:**")
                for title, url in doc_links.items():
                    st.markdown(f"- [{title}]({url})")
    # Other message types...
```

This method enhances the display of error messages by adding suggestions and documentation links based on the error type, providing a more helpful error experience for the user.

## Conclusion

The WebUI implementation includes responsive design, consistent styling, and enhanced error handling to provide a better user experience. These features ensure that the WebUI is usable on different devices, has a cohesive appearance, and provides helpful error messages with suggestions and documentation links.
## Implementation Status

.
