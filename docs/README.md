<div align="center">
  <a href="https://github.com/smit-8462/pyChai"><img src="../assets/pyChai_logo.svg" alt="pyChai" width="200"></a>
  <h1>pyChai</h1>
  <p align="center">
    <a href="https://github.com/smit-8462"><img src="https://img.shields.io/badge/Github_Profile-black?style=for-the-badge&logo=github" alt="GitHub Profile"></a>&nbsp;<a href="https://smit-8462.github.io/"><img src="https://img.shields.io/badge/Kaadya_Blog-f1e6ca?style=for-the-badge&logo=mocha" alt="Kaadya Blog"></a>&nbsp;<a href="https://www.linkedin.com/in/smit-bangare-b04176186/"><img src="https://img.shields.io/badge/LinkedIn_Profile-0077b5?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0nMjU2JyBoZWlnaHQ9JzI1NicgeG1sbnM9J2h0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnJyBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSd4TWlkWU1pZCcgdmlld0JveD0nMCAwIDI1NiAyNTYnPjxwYXRoIGQ9J00yMTguMTIzIDIxOC4xMjdoLTM3LjkzMXYtNTkuNDAzYzAtMTQuMTY1LS4yNTMtMzIuNC0xOS43MjgtMzIuNC0xOS43NTYgMC0yMi43NzkgMTUuNDM0LTIyLjc3OSAzMS4zNjl2NjAuNDNoLTM3LjkzVjk1Ljk2N2gzNi40MTN2MTYuNjk0aC41MWEzOS45MDcgMzkuOTA3IDAgMCAxIDM1LjkyOC0xOS43MzNjMzguNDQ1IDAgNDUuNTMzIDI1LjI4OCA0NS41MzMgNTguMTg2bC0uMDE2IDY3LjAxM1pNNTYuOTU1IDc5LjI3Yy0xMi4xNTcuMDAyLTIyLjAxNC05Ljg1Mi0yMi4wMTYtMjIuMDA5LS4wMDItMTIuMTU3IDkuODUxLTIyLjAxNCAyMi4wMDgtMjIuMDE2IDEyLjE1Ny0uMDAzIDIyLjAxNCA5Ljg1MSAyMi4wMTYgMjIuMDA4QTIyLjAxMyAyMi4wMTMgMCAwIDEgNTYuOTU1IDc5LjI3bTE4Ljk2NiAxMzguODU4SDM3Ljk1Vjk1Ljk2N2gzNy45N3YxMjIuMTZaTTIzNy4wMzMuMDE4SDE4Ljg5QzguNTgtLjA5OC4xMjUgOC4xNjEtLjAwMSAxOC40NzF2MjE5LjA1M2MuMTIyIDEwLjMxNSA4LjU3NiAxOC41ODIgMTguODkgMTguNDc0aDIxOC4xNDRjMTAuMzM2LjEyOCAxOC44MjMtOC4xMzkgMTguOTY2LTE4LjQ3NFYxOC40NTRjLS4xNDctMTAuMzMtOC42MzUtMTguNTg4LTE4Ljk2Ni0xOC40NTMnIGZpbGw9JyNmZmYnLz48L3N2Zz4K"></a>
  </p>
</div>


## Introduction

**pyChai** is a free open-source pyRevit extension for Autodesk Revit. It provides a collection of tools, optimizing certain tasks in a Revit workflow.  

For detailed documentation, visit [Kaadya](https://smit-8462.github.io/), where I showcase the journey of pyChai plugin, from ideation to pitfalls encountered along the way.

> Take a sip of chai🍵 and relax.

[Jump to Install section](#install)

---
## Tools

Currently, pyChai has following major tools under its arsenal, with more tools planned in future -

| Tool  | Notes  | Compatible  |
| :-- | :-- | :-- |
|  **Parameter Mapper**  |  <ul><li>Apply values on instance parameters of multiple Revit elements from a spreadsheet file.</ul></li><ul><li>For detailed documentation, [click here](https://smit-8462.github.io/posts/pychai-parameter-mapper/).</ul></li>  |  Revit 2020 till Revit 2027  |
<!-- |  Bulk Renamer  |  Rename family types (Built-in/Loaded) based on Revit type parameters  |  Revit 2020 - Revit 2027  | -->


### Parameter Mapper  

- The tool speed up the mundane data-entry tasks of applying Revit instance parameter values (string/numerical). 
- The values extracted from spreadsheet file (Excel/ LibreOffice Calc/CSV) are applied to Revit element's instance parameters.
- Users have choice to select Revit category, along with choice of Revit instance parameters for applying.
- The tool has data validation built-in, preventing the incorrect data type (string/float/integer/boolean).
- [Click here](https://smit-8462.github.io/posts/pychai-parameter-mapper/#notes) to learn more about the tool.
- [Click here](https://smit-8462.github.io/posts/pychai-parameter-mapper/#final-product) to view samples of Parameter Mapper.

<div class="video-container">
  <iframe
    src="https://www.youtube.com/embed/CXFiw9HfTFE"
    title="pyChai - Parameter Mapper"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen>
  </iframe>
</div>

---
## Install

There are 2 ways to install pyChai plugin -

<details open>
<summary>Powershell (recommended)</summary>

1. Launch Powershell.
2. Copy the code snippet shown below in the Powershell window - 
    ```powershell
   irm https://raw.githubusercontent.com/smit-8462/pyChai/main/scripts/pyChai_Extension_Install.ps1 | iex
    ```
   ![ManualInstall_00.png](../assets/ManualInstall_00.png)
3. Press Enter
4. If below message is displayed in terminal, `pyChai` extension has been successfully installed. ![ManualInstall_01.png](../assets/ManualInstall_00x1.png)
5. You can read Powershell script [here](https://github.com/smit-8462/pyChai/blob/main/scripts/pyChai_Extension_Install.ps1) in-depth for more information.

</details>


<details>
<summary>Manual installation</summary>

1. Click on `Code` button.  
    ![ManualInstall_01.png](../assets/ManualInstall_01.png)
2. Click on `Download ZIP`. It will download the pyChai extension `.zip` file.  
    ![ManualInstall_02.png](../assets/ManualInstall_02.png)
3. In File Explorer address bar, enter this folder location -
    ```md
    %appdata%\pyRevit
    ```
   ![ManualInstall_03.png](../assets/ManualInstall_03.png)
4. Go to `Extensions` folder. If it doesn't exist, create a folder named "Extensions".  
    ![ManualInstall_04.png](../assets/ManualInstall_04.png)
5. Create a folder named `pyChai.extension`.  
    ![ManualInstall_05.png](../assets/ManualInstall_05.png)
6. Extract the contents of recently downloaded `.zip` file to `pyChai.extension` folder.
7. Now, there will be a `python-packages-site-packages.zip` file in `bin\python_package_zip` folder location.
8. Extract the `python-packages-site-packages.zip` file contents in `pyChai.extension` folder.
9. In Revit, go to `pyRevit` tab. Click on `Reload` button.  
    ![ManualInstall_06.png](../assets/ManualInstall_06.png)
10. `pyChai` extension has been successfully installed. Congratulations 🎊! 

</details>


## Uninstall

There are 2 ways to uninstall/remove the pyChai plugin -

<details>
<summary>Command Prompt (recommended)</summary>

1. Launch Command Prompt.
2. Copy the code snippet shown below in the Command Prompt -  
    ```powershell
    pyrevit extensions delete pyChai
    ```
3. Press Enter.
4. `pyChai` extension has been successfully uninstalled. OUCH 🌧️!

</details>


<details>
<summary>Manual delete</summary>

1. Go to the following path, and delete the `pyChai.extension` folder - 
    ```md
    %appdata%\pyRevit\Extensions
    ```
2. In Revit, go to `pyRevit` tab. Click on `Reload` button.  
    ![ManualInstall_06.png](../assets/ManualInstall_06.png)
3. `pyChai` extension has been successfully uninstalled. OUCH 🌧️!

</details>

---
## Update

<details>
<summary>Update pyChai extension</summary>

1. Launch Command Prompt.
2. Copy the code snippet shown below in the Command Prompt -  
    ```powershell
    pyrevit extensions update pyChai
    ```
3. Press Enter
4. `pyChai` extension has been successfully updated. Congratulations 🎊!

</details>

---
## FAQ

> [!CAUTION]
> I am getting error - `ModuleNotFoundError: No module named 'pandas'`

<details>
<summary>Module import error</summary>

### Possible causes

1. The `site-packages` folder might be missing in `pyChai.extension` folder.
2. Some files or Python modules may be missing in `site-packages` folder.
3. Low possibility, due to update there might be change in folder structure.
4. The folder locations stored in `pyRevit_config.ini` file may be outdated/changed.

### Solution

<details open>
<summary>Solution 1 - Delete plugin configurations</summary>  
<br>

- Open the following file in Notepad
    ```txt
    %appdata%\pyRevit\pyRevit_config.ini
    ```
- Delete the lines containing `[pyChaiConfigs]`, `cpython_exe_location`, `cpython_plugin_lib_location` & `cpython_external_location` .
- Save the file and close it.
- Now, open the "Parameter Mapper" tool, and try again. It will work.
</details>

<br>

<details open>
<summary>Solution 2 - Replace Python module files</summary>  
<br>

- If issue is still unresolved, try the following steps.
- Delete `site-packages` folder in `pyChai.extension` folder (if any).
- Extract the contents of `.zip` file inside `bin\python_package_zip\` to the root (`pyChai.extension`) folder.
- In Revit, go to `pyRevit` tab. Click on `Reload` button.  
    ![ManualInstall_06.png](../assets/ManualInstall_06.png)
- Python modules have been replaced successfully.
- - Now, open the "Parameter Mapper" tool, and try again. It will work.
</details>

</details>
